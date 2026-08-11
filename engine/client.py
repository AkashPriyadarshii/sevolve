"""Judge/optimizer client — the agent itself.

The judge and optimizer ARE Claude Code, running with its own rules, patterns,
skills, and memory. Same executor pattern: shell `claude -p`. No separate
provider wiring. Tests mock subprocess.
"""

from __future__ import annotations

import shutil
import subprocess

from .executor import CLAUDE_CMD, ExecutorError


class ClaudeClient:
    def __init__(self, cmd: str = CLAUDE_CMD):
        self.cmd = cmd

    def complete(self, prompt: str) -> str:
        """One-shot call: run the prompt through the agent, return output."""
        if shutil.which(self.cmd) is None:
            raise ExecutorError(f"CLI '{self.cmd}' not on PATH — cannot judge/optimize.")
        proc = subprocess.run(
            [self.cmd, "-p", prompt, "--model", "sonnet"],
            capture_output=True,
            text=True,
            timeout=600,
            encoding="utf-8",
            errors="replace",
        )
        if proc.returncode != 0:
            raise ExecutorError(f"judge/optimizer exited {proc.returncode}: {proc.stderr[-2000:]}")
        return proc.stdout.strip()
