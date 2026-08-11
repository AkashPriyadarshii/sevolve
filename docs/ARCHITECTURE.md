# ARCHITECTURE — sevolve

## System boundaries
- **Engine** (Python, stdlib): owns loop, grading, optimization, gating, promotion, reporting.
- **Executor** (CLI boundary): the ONLY place a real agent is invoked. `executor.run()`; tests mock it.
- **Provider client**: hook point for judge/optimizer model calls. Offline by default (warns if unset).
- **Store** (filesystem): `artifacts/<kind>/<id>/v<N>.txt` + `meta.jsonl`. Git for VCS + PR promotion.

## Data flow
1. `evolve_artifact(store, artifact, eval_set, ctx, iterations, threshold, run_exec)`
2. For each iteration: run train task → capture Trace → grade (grader.evaluate + weighted_score) → if < threshold, build plan prompt → optimizer.propose variants.
3. Score each variant on held-out task. Track best.
4. Gates: size_limit + regression_holds + human/--ci. Promote if gated AND improved_overall (held-out score > initial).
5. Report → `report/report-<ts>.md`.

## Fault model
- Executor timeout/non-zero → trace.failure, output="", score 0 → loop continues (optimizer sees the failure).
- Judge non-JSON → score 0, rubric_ok=False → loop continues.
- Optimizer empty variants → no improvement → no promote (no churn).

## Non-goals
Weight training, fine-tuning, RL, GPU. Vercel/cloud lock-in. Closed services.
