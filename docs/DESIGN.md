# DESIGN — sevolve

## Architecture

```
CLI ──> loop.evolve_artifact ──> executor (claude -p adapter)
        │  ├── trace capture (JSONL)
        │  ├── grader (blind, separate)
        │  └── judge (LLM-as-judge, blind)
        └── optimizer (GEPA-lite reflect-propose)
        └── gate (size / regression / human / --ci)
        └── promote (held-out score up → version bump)
```

## Key decisions
1. **Standalone orchestrator** shells `claude -p`. Hooks/ = optional trace source. Executor is the only CLI coupling; tests mock it.
2. **Git is the store.** Artifact content = real files; meta.jsonl alongside. Rollback + review for free.
3. **Blind grader.** Evaluator sits outside the loop. Reward-hacking defense.
4. **Promote only on real gain.** Held-out score must rise.
5. **Train/validate split.** Held-out task used for promotion; train task for feedback. Prevents overfit (GEPA lesson).
6. **Capability guardrail** — weak judge logs a warning, never silent churn.

## Modules (engine/, stdlib-only)
| module | job |
|--------|-----|
| artifact.py | versioned store, status, idempotent scoring |
| trace.py | capture/save/render |
| executor.py | CLI adapter |
| grader.py | hard deterministic checks |
| judge.py | blind LLM-as-judge, JSON parse |
| optimizer.py | GEPA-lite reflect-propose |
| gate.py | size/regression/human gates |
| loop.py | orchestration |
| report.py | before/after markdown |

## Upgrade paths (ponytail markers)
- Optimizer: reflect-propose → genetic ops (crossover/tournament) + Pareto selection when overfit appears.
- Executor: `claude -p` → configurable command.
- Gates: add candidate's own test-suite gate when artifacts grow tests.

## Safety
Evaluator + permission control sit OUTSIDE the loop. `--ci` skips human, never mechanical gates.
