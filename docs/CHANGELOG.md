# CHANGELOG — sevolve

## 0.1.0 (2026-08-12) — finalized
- P0 scaffold: git init (identity pinned), pyproject (stdlib-only), MIT LICENSE, README, .gitignore.
- P1: artifact versioned store (create/add_version/get/rollback/set_score idempotent/set_status/list), trace capture/save/render, executor CLI adapter.
- P2: graders (exact/contains/length, blind), judge (blind LLM-as-judge, JSON parse, non-JSON fallback), seed eval set + generator.
- P3: GEPA-lite optimizer (reflect-propose), gates (size/regression/human/--ci), loop.evolve_artifact, report (before/after + REGRESSION), CLI (evolve/artifact-add/artifacts/seed-report).
- P4: hermetic test suite — 18 pass, no network/key. Loop verifies bad-seed → held-out score UP; no churn on no-improvement.
- P4.1: judge/optimizer client = the agent itself (`engine/client.py`, `claude -p`, read-only plan mode).
- P4.2: GitHub Pages deploy workflow. Fixed Pages enablement + un-ignored `site/index.html` (was breaking the artifact archive step).
- P4.3: repo skeleton docs — AGENTS.md, STATE.md, session-handoff.md, docs/HANDOFF.md.

## Known limitations
- Executor hardcoded `claude -p` + sonnet. Configurable command = next.
- Judge/optimizer client wiring is a hook point, not yet a wired provider.
- Seed evals: 2 tasks, concise-summary domain.
- Promotion is a local version bump, not yet a PR (P5).
- No real-session trace capture yet (P5).
