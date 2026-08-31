"""Real-session trace ingestion.

Ingests real execution logs from Claude Code, OpenClaw, and generic JSONL traces
into standardized Trace objects for the sevolve evolution loop.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .trace import FAILURE, OUTPUT, TOOL_CALL, Trace, save


def parse_claude_transcript(text: str) -> list[Trace]:
    """Parse Claude Code session JSONL logs into Trace instances."""
    traces: list[Trace] = []
    current_task = ""
    current_events: list[dict[str, Any]] = []
    current_output = ""
    ok = True

    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            entry = json.loads(line)
        except json.JSONDecodeError:
            continue

        # Detect message type in Claude Code format
        msg_type = entry.get("type", "")
        role = entry.get("role", "")
        content = entry.get("content", "")

        if msg_type in {"USER_INPUT", "user"} or role == "user":
            user_text = str(content) if isinstance(content, str) else json.dumps(content)
            # If we had a prior task in flight, commit it as a trace
            if current_task and (current_events or current_output):
                traces.append(
                    Trace(
                        task=current_task,
                        events=list(current_events),
                        output=current_output,
                        ok=ok,
                    )
                )
                current_events = []
                current_output = ""
                ok = True
            current_task = user_text

        elif msg_type in {"PLANNER_RESPONSE", "assistant"} or role == "assistant":
            resp_text = str(content) if isinstance(content, str) else ""
            current_output = resp_text

            # Parse tool calls
            tool_calls = entry.get("tool_calls", [])
            if isinstance(tool_calls, list):
                for tc in tool_calls:
                    if isinstance(tc, dict):
                        tname = tc.get("name", tc.get("toolAction", "tool"))
                        targs = json.dumps(tc.get("arguments", tc.get("parameters", "")))
                        current_events.append({"kind": TOOL_CALL, "name": tname, "args": targs, "result": ""})

            # Detect failure signals in entry status
            status = entry.get("status", "")
            if status in {"ERROR", "FAILED", "failed", "error"}:
                ok = False
                current_events.append({"kind": FAILURE, "reason": "status_error", "detail": str(entry.get("error", ""))})

        elif msg_type in {"TOOL_RESULT", "tool"}:
            tresult = str(content) if isinstance(content, str) else json.dumps(content)
            is_error = bool(entry.get("is_error", False))
            if is_error:
                ok = False
                current_events.append({"kind": FAILURE, "reason": "tool_error", "detail": tresult[:500]})
            else:
                current_events.append({"kind": TOOL_CALL, "name": "result", "args": "", "result": tresult[:500]})

    if current_task:
        traces.append(
            Trace(
                task=current_task,
                events=current_events,
                output=current_output,
                ok=ok,
            )
        )

    return traces


def parse_generic_jsonl(text: str) -> list[Trace]:
    """Parse standard sevolve or generic JSONL trace files."""
    traces: list[Trace] = []
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            d = json.loads(line)
            if isinstance(d, dict) and "task" in d:
                traces.append(Trace.from_dict(d))
        except (json.JSONDecodeError, TypeError):
            continue
    return traces


def ingest_file(source_path: Path | str, traces_dir: Path | str = "traces") -> list[str]:
    """Ingests a file (Claude transcript or generic JSONL) and saves traces to traces_dir."""
    p = Path(source_path)
    if not p.exists():
        raise FileNotFoundError(f"source file not found: {source_path}")

    content = p.read_text(encoding="utf-8", errors="replace")
    # First try generic trace parse
    traces = parse_generic_jsonl(content)
    # If not in generic format, parse as Claude Code transcript
    if not traces:
        traces = parse_claude_transcript(content)

    saved_ids = []
    for t in traces:
        tid = save(t, traces_dir=traces_dir)
        saved_ids.append(tid)

    return saved_ids
