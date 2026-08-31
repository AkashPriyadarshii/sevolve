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

## 0.1.1 (2026-08-31) - audit & P5 completion
- Ponytail code audit: eliminated side-effecting `mkdir` on read, consolidated client/executor into stdlib runners, single-pass metadata writes.
- Robust JSON extraction: handles markdown code fences (` ```json `) and raw outputs seamlessly across judge and optimizer.
- Trace ingestion: added `engine/ingest.py` to parse live Claude Code transcripts (`USER_INPUT`, `PLANNER_RESPONSE`, `TOOL_RESULT`) and generic JSONL logs into `Trace` objects.
- PR promotion: hardened `engine/promote.py` report parsing and wired `sevolve promote` subcommand.
- CLI subcommands: added `sevolve ingest`, `sevolve promote`, and `sevolve doctor`.
- Test suite expanded: 18 -> 32 hermetic tests (100% passing, 0.39s runtime).

## 0.2.0 (2026-08-31) - Self-Evolving Code Graph & Cognitive Brain
- Dual-Layer Architecture: Introduced Structural Code Graph (AST, calls, imports) + Cognitive Brain (traces, failures, fixes, rules).
- SQLite WAL + FTS5 Backend: Sub-5ms queries and recursive SQL CTE multi-hop graph walks in `.sevolve/brain.db`.
- Hebbian Evolution: Edge weight reinforcement on success ($\alpha=0.15$), attenuation on failure ($\beta=0.20$), dynamic half-life decay, and pruning.
- Universal Agent MCP Server: Stdio JSON-RPC 2.0 interface (`search_brain`, `get_context_map`, `record_trace`, `suggest_fixes`) for Claude Code, Cursor, OpenClaw, Codex, Windsurf, and Antigravity.
- Obsidian Vault Sync: Bi-directional markdown sync with YAML frontmatter and `[[WikiLinks]]` in `.sevolve/vault/`.
- CLI Workbench: Added `sevolve brain scan`, `query`, `map`, `sync`, `prune`.
