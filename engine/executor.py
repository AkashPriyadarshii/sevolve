"""Executor — runs a task with the current artifact.

The only place the engine touches a real agent CLI. Everything else is
isolated from CLI drift: if `claude -p` flags change, this is the one file
to fix. Tests mock `run()` so the suite never needs a network or a key.
"""

from __future__ import annotations

import shutil
import subprocess
import sys

from .trace import FAILURE, TOOL_CALL, Trace

CLAUDE_CMD = "claude"


class ExecutorError(RuntimeError):
    pass


def _prompt(artifact: dict, task: str) -> str:
    kind = artifact["kind"]
    if kind == "skill":
        head = (
            "You are an agent that uses the following SKILL instructions. "
            "Follow them exactly.\n\n---SKILL---\n"
            f"{artifact['content']}\n---END SKILL---\n\n"
        )
    elif kind == "prompt":
        head = f"You are an agent executing a task. Your instructions:\n\n{artifact['content']}\n\n"
    elif kind == "rule":
        head = f"You are an agent. A system rule applies:\n\n{artifact['content']}\n\n"
    else:  # tool_desc
        head = f"You are an agent. A tool is available to you:\n\n{artifact['content']}\n\n"
    return head + f"TASK: {task}\n\nReturn only the result."


class ClaudeClient:
    def __init__(self, cmd: str = CLAUDE_CMD, model: str = "sonnet"):
        self.cmd = cmd
        self.model = model

    def complete(self, prompt: str) -> str:
        """One-shot call: run the prompt through the agent, return output."""
        if shutil.which(self.cmd) is None:
            raise ExecutorError(f"CLI '{self.cmd}' not on PATH — cannot judge/optimize.")
        proc = subprocess.run(
            [self.cmd, "-p", prompt, "--model", self.model, "--permission-mode", "plan"],
            capture_output=True,
            text=True,
            timeout=600,
            encoding="utf-8",
            errors="replace",
        )
        if proc.returncode != 0:
            raise ExecutorError(f"judge/optimizer exited {proc.returncode}: {proc.stderr[-2000:]}")
        return proc.stdout.strip()


def run(artifact: dict, task: str, trace: Trace | None = None, timeout: int = 300) -> str:
    """Run the task with the artifact. Returns output text.

    If `trace` is given, captures tool calls and failures into it (best-effort:
    we can't see the agent's internal tool calls via `claude -p`, so we record
    the call boundary and any failure).
    """
    cmd = CLAUDE_CMD
    if shutil.which(CLAUDE_CMD) is None:
        raise ExecutorError(
            f"CLI '{CLAUDE_CMD}' not on PATH. Install it or set executor.CLAUDE_CMD. "
            "This is the only network/CLI touchpoint — tests mock run()."
        )
    argv = [cmd, "-p", _prompt(artifact, task), "--model", "sonnet"]
    try:
        if trace is not None:
            trace.tool("executor", args=cmd)
        proc = subprocess.run(
            argv,
            capture_output=True,
            text=True,
            timeout=timeout,
            encoding="utf-8",
            errors="replace",
        )
    except subprocess.TimeoutExpired:
        if trace is not None:
            trace.failure("timeout", f"executor exceeded {timeout}s")
        raise ExecutorError(f"executor timed out after {timeout}s") from None
    except FileNotFoundError as e:
        raise ExecutorError(f"failed to launch {cmd}: {e}") from None

    if proc.returncode != 0:
        if trace is not None:
            trace.failure("non-zero exit", proc.stderr[-2000:])
        raise ExecutorError(
            f"executor exited {proc.returncode}: {proc.stderr[-2000:]}"
        )

    out = proc.stdout.strip()
    if trace is not None:
        trace.add("output", text=out)
        trace.ok = True
    return out
