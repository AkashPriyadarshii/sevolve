# CLAUDE.md — sevolve

## What this is
FOSS self-evolving harness for LLM agents. Evolves versioned artifacts (skills, prompts, tool descriptions, rules) from real execution traces. No GPU, no weight training, MIT, stdlib-only runtime.

## Engine loop
sample task → run with current artifact → capture trace → blind grade → below threshold? → optimizer reflects on trace → propose ≤3 variants → gates (size/regression/tests/human) → promote best on held-out → version bump.

## Hard rules
- Grader + judge run blind and separate — never see the proposed diff (reward-hacking defense).
- Promote only on real improvement (held-out score up). Never churn redundant versions.
- `--ci` overrides human approval, never the mechanical gates.
- The evaluator sits outside the evolution loop (Lilian Weng).
- All tests hermetic — no network, no API key. Run `python -m pytest -q` locally, always.

## Layout
- engine/ — cli, artifact, trace, executor, grader, judge, optimizer, gate, loop, report (stdlib)
- evals/ — seed task set + generator (BYOT path)
- traces/ — captured JSONL
- artifacts/ — versioned content + meta.jsonl
- site/ — static marketing site (zero build)
- docs/ — PRD, DESIGN, ARCHITECTURE, HANDOFF, CHANGELOG

## Status
- [x] P0 scaffold (git, pyproject, LICENSE, README)
- [x] P1 artifact/trace/executor
- [x] P2 graders + judge + seed evals
- [x] P3 optimizer + gates + loop + report + CLI
- [x] P4 hermetic tests (15 pass)
- [ ] P5 real-session traces (hooks) + PR promote + demo

## Git
Identity pinned: user.name AkashPriyadarshii, noreply email. GitHub work via `gh`, never raw curl. Attribution disabled globally.
