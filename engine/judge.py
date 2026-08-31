"""LLM-as-judge — rubric-driven quality score with written reasoning.

Blind by design: the judge sees the task, the trace, and the output — never
the candidate artifact. It returns a 0..1 score plus reasoning the optimizer
consumes. The score alone would let the optimizer game it; the reasoning is
the signal that actually improves the artifact.

Runs offline (scripted) in tests. Real mode uses the model provider passed in.
"""

from __future__ import annotations

import json
from typing import Any, Callable

from .trace import trace_to_text

Judge = Callable[[str, dict[str, Any]], dict[str, Any]]
# ^ (prompt: str, ctx) -> {"score": 0..1, "reasoning": str, "rubric_ok": bool}

RUBRIC = """Score 0..1 on:
- Accuracy (does the output do what the task asked)
- Completeness (nothing material missing)
- Following any constraints in the task
Be strict. Return JSON only: {"score": float, "reasoning": str, "rubric_ok": bool}
reasoning = written critique the optimizer will read. rubric_ok = was the rubric followed."""


def build_prompt(task: str, trace, output: str) -> str:
    return (
        "You are a strict grader. Grade the OUTPUT for the TASK below.\n\n"
        f"TASK:\n{task}\n\n"
        f"TRACE (what the agent did):\n{trace_to_text(trace) if trace is not None else '(no trace)'}\n\n"
        f"OUTPUT:\n{output}\n\n"
        f"{RUBRIC}"
    )


def extract_json(raw: str) -> dict[str, Any] | None:
    if not raw or not isinstance(raw, str):
        return None
    s = raw.strip()
    if s.startswith("```"):
        lines = s.splitlines()
        if len(lines) >= 2 and lines[-1].strip().startswith("```"):
            s = "\n".join(lines[1:-1]).strip()
    try:
        data = json.loads(s)
        if isinstance(data, dict):
            return data
    except (json.JSONDecodeError, TypeError):
        pass
    start = raw.find("{")
    end = raw.rfind("}")
    if start != -1 and end != -1 and end > start:
        try:
            data = json.loads(raw[start : end + 1])
            if isinstance(data, dict):
                return data
        except (json.JSONDecodeError, TypeError):
            pass
    return None


def run_judge(prompt: str, ctx: dict[str, Any]) -> dict[str, Any]:
    """Call a judge model. `ctx['client']` provides .complete(prompt)->str.
    Override ctx['client'] with a scripted judge in tests.
    """
    client = ctx.get("client")
    if client is None:
        raise RuntimeError("judge client not provided (see ctx['client'])")
    raw = client.complete(prompt)
    parsed = extract_json(raw)
    if parsed is None:
        return {"score": 0.0, "reasoning": f"judge returned non-JSON: {raw[:300]}", "rubric_ok": False}
    return {
        "score": float(parsed.get("score", 0.0)),
        "reasoning": str(parsed.get("reasoning", "")),
        "rubric_ok": bool(parsed.get("rubric_ok", True)),
    }


def judge_score(result: dict[str, Any]) -> float:
    return max(0.0, min(1.0, result.get("score", 0.0)))
