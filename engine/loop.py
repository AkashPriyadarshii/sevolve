"""The evolution loop — orchestrates the full cycle for one artifact.

Kept separate from cli.py so it's importable and testable. `evolve_artifact`
is the whole engine: sample task, run, grade, and if below threshold, propose
variants, gate the best on a held-out task, promote.
"""

from __future__ import annotations

from typing import Any

from .artifact import ArtifactStore, PROMOTED
from .executor import ExecutorError, run
from .grader import evaluate, weighted_score
from .judge import build_prompt, run_judge
from .optimizer import build_plan_prompt, propose
from .trace import Trace, save


def evolve_artifact(
    store: ArtifactStore,
    artifact: dict[str, Any],
    eval_set: dict[str, Any],
    ctx: dict[str, Any],
    iterations: int = 3,
    threshold: float = 0.85,
    run_exec: Any = run,
) -> dict[str, Any]:
    """Run the loop. ctx carries clients/gates/ci flag. Returns run summary.

    eval_set: {"artifact": {...}, "tasks": [{"id", "task", "graders": {...}, ...}]}
    Run order: train task for feedback, held-out task for promotion.
    """
    tasks = eval_set.get("tasks", [])
    if len(tasks) < 2:
        raise ValueError("need >=2 tasks: a train task and a held-out task")
    train, held = tasks[0], tasks[-1]
    graders = train["_graders"]
    held_graders = held.get("_graders", graders)

    kind, aid = artifact["kind"], artifact["id"]
    current = artifact
    best = current
    best_score = _score_artifact(run_exec, current, held, held_graders, ctx)

    history = []
    for i in range(iterations):
        trace = Trace(task=train["task"])
        try:
            output = run_exec(current, train["task"], trace=trace)
        except ExecutorError as e:
            trace.failure("executor error", str(e))
            output = ""
        grades = evaluate(graders, train["task"], trace, output)
        score = weighted_score(grades)
        trace_ids = []
        if output:
            trace_ids = [save(trace)]
        judge_result = _judge(ctx, train["task"], trace, output)

        improved = False
        if score < threshold:
            plan = build_plan_prompt(current, train["task"], trace, output, grades, judge_result)
            variants = propose(plan, ctx)
            for v in variants:
                cand = {**current, "content": v["content"]}
                held_score = _score_artifact(run_exec, cand, held, held_graders, ctx)
                if held_score > best_score:
                    best = cand
                    best_score = held_score
                    best["rationale"] = v.get("rationale", "")
                    improved = True

        history.append({"iter": i + 1, "train_score": score, "best_held": best_score,
                        "improved": improved, "traces": trace_ids,
                        "judge_reasoning": judge_result.get("reasoning", "")})

        current = best if improved else current
        if improved and best_score >= threshold:
            break

    # gates run against the best candidate found (or original if none better)
    final = best
    final_score = best_score
    # promote only on real improvement — never churn a redundant version
    initial = _score_artifact(run_exec, artifact, held, held_graders, ctx)
    improved_overall = final_score > initial + 1e-9
    gated, gate_results = _run_gates(ctx, final, final_score, current)

    promoted = False
    if gated and improved_overall:
        parent = store.meta(kind, aid)[-1]["version"] if store.meta(kind, aid) else None
        store.add_version(
            kind,
            aid,
            final["content"],
            parent=parent,
            status=PROMOTED,
            score=final_score,
            grades={},
            trace_ids=[],
        )
        promoted = True

    return {
        "artifact": {"kind": kind, "id": aid, "version": best["version"] if best is not None else None},
        "promoted": promoted,
        "best_score": round(final_score, 3),
        "gate_results": gate_results,
        "history": history,
    }


def _score_artifact(run_exec, artifact, task: dict, graders, ctx) -> float:
    trace = Trace(task=task["task"])
    try:
        output = run_exec(artifact, task["task"], trace=trace)
    except ExecutorError:
        output = ""
    if not output:
        return 0.0
    grades = evaluate(graders, task["task"], trace, output)
    return weighted_score(grades)


def _judge(ctx, task, trace, output):
    try:
        prompt = build_prompt(task, trace, output)
        return run_judge(prompt, ctx)
    except Exception as e:  # judge failure must not kill the loop
        return {"score": 0.0, "reasoning": f"judge error: {e}", "rubric_ok": False}


def _run_gates(ctx, artifact, score, current) -> tuple[bool, list[tuple[str, str]]]:
    from .gate import human_approval, run_gates, regression_holds, size_limit
    gates = [
        size_limit(ctx.get("max_size", 16_000)),
        regression_holds(current.get("score") if current.get("score") else 0.0),
    ]
    if ctx.get("ci"):
        gates.append(human_approval(prompt_fn=lambda c: True))
    else:
        gates.append(human_approval())
    gate_ctx = {"artifact": artifact, "new_score": score, "ci": ctx.get("ci", False)}
    return run_gates(gates, gate_ctx)
