"""End-to-end loop verification (P3).

The core claim: with a bad seed skill, the engine SCORES UP on held-out data
after evolution, and the report shows it. The executor is mocked (no network)
and the judge/optimizer are scripted (deterministic).
"""

from engine.artifact import PROMOTED
from engine.grader import make_contains
from engine.loop import evolve_artifact


def _bad_seed() -> str:
    return "Answer briefly."  # known-bad: no date/number/length discipline


def _good_variant() -> str:
    return (
        "1. Keep the main point. 2. Keep exact dates and numbers. "
        "3. Hard cap: max 40 words. 4. No padding or preamble."
    )


def _executor_with(artifact, task, trace=None, timeout=300):
    # Simulates the executor: applies the artifact's skill to the task.
    if trace is not None:
        trace.tool("executor", args="claude -p")
        trace.ok = True
    good = artifact["content"]
    if "max 40 words" in good or "Hard cap" in good:
        # good skill -> disciplined output carrying the key token
        if "2026-07-15" in task:
            out = "RBI cut repo rates on 2026-07-15. The move was a surprise."
        else:
            out = "64% of enterprises run most workloads in public cloud now."
    else:
        out = "rates changed, cloud usage high"  # bad skill -> misses key facts
    if trace is not None:
        trace.add("output", text=out)
    return out


def _optimizer_client():
    import json

    class Client:
        def complete(self, prompt):
            if "GRADER SCORES" in prompt:
                return json.dumps({
                    "critique": "skill had no explicit caps, output lost key facts.",
                    "variants": [
                        {"content": _good_variant(), "rationale": "adds caps + fact discipline"},
                    ],
                })
            return json.dumps({"score": 0.95, "reasoning": "accurate and concise", "rubric_ok": True})

    return Client()


def _held_grader():
    return {"contains_64": make_contains("64")}


def test_loop_scores_up_on_heldout(store, seed_eval_set):
    # Make held-out (sum-2) use a strict grader so improvement is measurable.
    seed_eval_set["tasks"][1]["_graders"] = _held_grader()
    store.create("skill", "concise-summary", _bad_seed())
    artifact = store.get("skill", "concise-summary")

    ctx = {"client": _optimizer_client(), "ci": True, "max_size": 16_000}
    result = evolve_artifact(
        store, artifact, seed_eval_set, ctx,
        iterations=3, threshold=0.85, run_exec=_executor_with,
    )

    assert result["promoted"] is True
    assert result["best_score"] >= 0.85
    # verify the promoted version is the good variant
    meta = store.meta("skill", "concise-summary")
    promoted = [m for m in meta if m["status"] == PROMOTED]
    assert promoted, "expected a promoted version"
    assert store.get_version("skill", "concise-summary", promoted[-1]["version"])["content"] == _good_variant()


def test_loop_no_degradation_without_improvement(store, seed_eval_set, ctx, make_executor):
    # If the optimizer proposes nothing better, we must NOT churn versions.
    class NoImprove:
        def complete(self, prompt):
            import json
            if "GRADER SCORES" in prompt:
                return json.dumps({"critique": "n/a", "variants": []})
            return json.dumps({"score": 0.5, "reasoning": "ok", "rubric_ok": True})

    store.create("skill", "s", _good_variant())
    artifact = store.get("skill", "s")
    run_exec = _executor_with
    # use the good variant executor so baseline already high; optimizer offers nothing
    result = evolve_artifact(store, artifact, seed_eval_set, ctx_with_client(NoImprove()),
                             iterations=2, threshold=0.99, run_exec=run_exec)
    # threshold 0.99 never reached -> not promoted even though high score
    assert result["promoted"] is False
    assert result["best_score"] >= 0.85


def ctx_with_client(client):
    return {"client": client, "ci": True, "max_size": 16_000}
