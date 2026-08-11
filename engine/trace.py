"""Execution trace capture and replay.

A trace is what actually happened during one task run: the task, the tool
calls, failures, and the final output. Traces are the raw material the
optimizer reads to understand why an artifact failed.
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any

TASK, TOOL_CALL, FAILURE, OUTPUT = "task", "tool_call", "failure", "output"


@dataclass
class Trace:
    task: str
    events: list[dict[str, Any]] = field(default_factory=list)
    output: str = ""
    ok: bool = False
    created_at: str = ""

    def __post_init__(self) -> None:
        if not self.created_at:
            self.created_at = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

    def add(self, kind: str, **payload: Any) -> None:
        self.events.append({"kind": kind, **payload})

    def failure(self, reason: str, detail: str = "") -> None:
        self.add(FAILURE, reason=reason, detail=detail)

    def tool(self, name: str, args: str = "", result: str = "") -> None:
        self.add(TOOL_CALL, name=name, args=args, result=result)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "Trace":
        return cls(**d)


def save(trace: Trace, traces_dir: Path | str = "traces") -> str:
    """Write one trace as a JSONL line. Returns the trace id."""
    traces_dir = Path(traces_dir)
    traces_dir.mkdir(parents=True, exist_ok=True)
    tid = time.strftime("%Y%m%dT%H%M%S", time.gmtime())
    path = traces_dir / f"{tid}.jsonl"
    path.write_text(json.dumps(trace.to_dict()) + "\n", encoding="utf-8")
    return tid


def load_all(traces_dir: Path | str = "traces") -> list[tuple[str, Trace]]:
    out = []
    for p in sorted(Path(traces_dir).glob("*.jsonl")):
        for line in p.read_text(encoding="utf-8").splitlines():
            if line:
                out.append((p.stem, Trace.from_dict(json.loads(line))))
    return out


def trace_to_text(t: Trace) -> str:
    """Human-readable rendering of a trace — what the optimizer and judge read."""
    lines = [f"TASK: {t.task}", ""]
    for e in t.events:
        if e["kind"] == TOOL_CALL:
            lines.append(f"TOOL {e['name']} args={e['args']!r} result={e['result']!r}")
        elif e["kind"] == FAILURE:
            lines.append(f"FAILED reason={e['reason']!r} detail={e['detail']!r}")
        else:
            lines.append(f"{e['kind']}: {e}")
    lines.append(f"OUTPUT: {t.output}")
    lines.append(f"OK: {t.ok}")
    return "\n".join(lines)
