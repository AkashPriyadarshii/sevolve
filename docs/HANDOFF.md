# HANDOFF — sevolve

Shorter pointer for anyone landing mid-project. Full context: STATE.md, session-handoff.md, PRD.md, ARCHITECTURE.md.

## What exists
Self-evolving harness for LLM agents. Versioned artifacts (skills, prompts, tool descriptions, rules) evolved from real execution traces. Stdlib-only Python engine. Git is the store. Site is static HTML on GitHub Pages.

## Working pieces
- Engine loop: `engine/loop.py` → `evolve_artifact`. Train/validate split, blind grader, GEPA-lite optimizer, gates, held-out promote.
- CLI: `sevolve evolve|artifact-add|artifacts|seed-report`.
- Judge/optimizer = the agent itself (`engine/client.py`, shells `claude -p`, read-only plan mode).
- Tests: 18 hermetic, no network/key. `python -m pytest -q`.

## Known gaps
- Executor hardcoded `claude -p` + sonnet — configurable command next.
- No real-session trace capture yet (P5).
- No PR-promote path yet (P5) — promotion is local version bump.

## Getting to v0.2.0
P5 (hooks + PR promote + demo) → then: configurable executor command, wider seed eval set, real trace corpus.
