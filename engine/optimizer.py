"""GEPA-lite optimizer — read the trace, explain why it failed, propose variants.

MVP is reflect-propose: the optimizer gets {task, trace, grader reasoning,
output} and writes a natural-language critique, then proposes <=3 candidate
content variants, each with a one-line rationale. Full genetic operations
(crossover, tournament) are the upgrade path — see ponytail note at the end.
"""

from __future__ import annotations

from typing import Any, Callable

from .trace import trace_to_text

# Optimizer fn: (task, trace, output, grades, judge_result, artifact) -> [{"content", "rationale"}]
Optimizer = Callable[..., list[dict[str, str]]]

PLAN_TEMPLATE = """You are evolving a skill. A task run using the current skill did not score well.

CURRENT SKILL:
{artifact}

TASK:
{task}

TRACE (what the agent did):
{trace}

OUTPUT:
{output}

GRADER SCORES (name: score):
{grades}

JUDGE REASONING:
{judge}

Explain in 2-4 sentences WHY the skill produced a poor result (be specific: which instruction is missing, ambiguous, or wrong). Then propose up to 3 improved skill variants. Each variant is the FULL replacement skill content.

Return JSON only:
{{"critique": str, "variants": [{{"content": str, "rationale": str}}]}}"""


def build_plan_prompt(artifact: dict, task: str, trace, output: str,
                      grades: dict[str, float], judge_result: dict[str, Any]) -> str:
    return PLAN_TEMPLATE.format(
        artifact=artifact["content"],
        task=task,
        trace=trace_to_text(trace) if trace is not None else "(no trace)",
        output=output,
        grades=", ".join(f"{k}={v}" for k, v in grades.items()),
        judge=judge_result.get("reasoning", "(no reasoning)"),
    )


def propose(plan_prompt: str, ctx: dict[str, Any]) -> list[dict[str, str]]:
    """Call the optimizer model. ctx['client'] provides .complete(prompt)->str.
    Override in tests with a scripted optimizer.
    """
    import json

    client = ctx.get("client")
    if client is None:
        raise RuntimeError("optimizer client not provided (see ctx['client'])")
    raw = client.complete(plan_prompt)
    try:
        parsed = json.loads(raw)
    except (json.JSONDecodeError, TypeError):
        return []
    variants = parsed.get("variants", [])
    return [
        {"content": str(v.get("content", "")), "rationale": str(v.get("rationale", ""))}
        for v in variants
        if v.get("content")
    ]


# ponytail: MVP is reflect-propose only. Add crossover/tournament + Pareto
# selection when the naive best-variant pick starts overfitting to a single
# task (diversity collapse). That's the documented upgrade path.
