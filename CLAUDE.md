# CLAUDE.md — sevolve

## What this is
FOSS Self-Evolving Code Graph & Cognitive Brain for LLM agents. Combines a structural AST code graph (symbols, calls, imports) with an evolving cognitive brain (traces, rules, failures, fixes) using Hebbian edge dynamics. Zero GPU, zero third-party dependencies, MIT, stdlib-only SQLite WAL + FTS5 runtime.

## Core Loop & Dual-Layer Brain
1. **Structural Code Graph (Layer 1)**: AST parser extracts functions, classes, files, signatures, and call/import dependencies into SQLite. Token-budgeted PageRank maps.
2. **Cognitive Evolving Brain (Layer 2)**: Ingests traces from Claude Code, OpenClaw, and agents. Links failures to fixes and rules.
3. **Hebbian Dynamics**: Reinforces successful symbol-rule edges ($\alpha=0.15$), attenuates failing paths ($\beta=0.20$), decays over time, prunes dead links.
4. **Universal Connectors**: Native stdio JSON-RPC MCP server (`search_brain`, `get_context_map`, `record_trace`, `suggest_fixes`), CLI (`sevolve brain ...`), and bi-directional Obsidian Markdown vault (`.sevolve/vault/`).

## Hard Rules
- **Zero Third-Party Dependencies**: Pure Python stdlib (`sqlite3`, `ast`, `json`, `re`, `argparse`).
- **SQLite WAL + FTS5**: Sub-5ms queries, single-file `.sevolve/brain.db`.
- **Hermetic Test Floor**: All tests run offline with `python -m pytest -q`.
- **Non-destructive Ingestion**: Never mutate original code during passive scanning; evolve brain edges dynamically.

## Layout
- `engine/brain/` — SQLite graph DB, AST parser, Hebbian dynamics, PageRank, MCP server, Obsidian vault.
- `engine/` — CLI, harness, trace ingestion, gates, runner.
- `evals/` — Seed task sets and eval generators.
- `traces/` — Captured JSONL execution traces.
- `artifacts/` — Versioned skills/prompts/rules + metadata.
- `site/` — Static marketing site (zero build).
- `docs/` — PRD, DESIGN, ARCHITECTURE, HANDOFF, CHANGELOG.

## Git & Auth
Pinned identity: AkashPriyadarshii. GitHub automation via `gh`. Conventional commits, terse messages, zero AI buzzwords.
