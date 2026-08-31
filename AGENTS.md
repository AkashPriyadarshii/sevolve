# AGENTS.md — sevolve

Rules for any agent working in this repository.

## Hard Invariants
- **Zero Third-Party Dependencies** — Python stdlib only (`sqlite3`, `ast`, `json`, `re`, `argparse`).
- **SQLite WAL + FTS5 Storage** — All graph nodes, edges, and full-text indexes live in `.sevolve/brain.db`.
- **Dual-Layer Graph Separation** — Structural AST edges (`CALLS`, `IMPORTS`) are deterministic; Cognitive edges (`CO_MODIFIED_WITH`, `FAILED_ON`, `FIXED_BY`, `APPLIES_TO`) evolve via Hebbian dynamics.
- **Hebbian Evolution Rules** — Strengthen edges on success ($\alpha=0.15$), attenuate on failure ($\beta=0.20$), decay over time, prune dead links.
- **Universal Interoperability** — Native stdio JSON-RPC MCP server + CLI + bi-directional Obsidian Markdown vault (`.sevolve/vault/`).
- **All Tests Hermetic** — Run `python -m pytest -q` locally before every commit. Zero network/API keys needed.

## Touch Map
| Area | Rule |
|------|------|
| `engine/brain/` | Graph engine: SQLite DB, AST parser, Hebbian dynamics, PageRank, MCP server, Obsidian vault. |
| `engine/` | Core harness, CLI, trace ingestion, gates, runner. Pure stdlib. |
| `tests/` | 100% hermetic unit & integration tests. |
| `site/` | Static HTML marketing site (zero build, deploy archives it). |
| `docs/` | Architectural specs, PRD, and changelog. Keep terse. |

## Workflow
1. Understand the data flow before touching code.
2. Changes must preserve <5ms query times and <5MB RAM footprint.
3. Keep test suite 100% green: `python -m pytest -q`.
4. Commit conventional, push via `gh` after user confirmation.
