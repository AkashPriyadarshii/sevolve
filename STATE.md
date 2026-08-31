# STATE - sevolve

Updated 2026-08-31. Single source of truth for repository state.

## Version
**0.2.0-dev** — Architecture: **Self-Evolving Code Graph & Cognitive Brain**.
- Sub-5ms queries via SQLite WAL + FTS5 trigram indexing.
- Zero external dependencies (stdlib-only: `sqlite3`, `ast`, `json`, `re`, `argparse`).
- Universal stdio JSON-RPC MCP server + CLI + Obsidian Markdown vault (`.sevolve/vault/`).

## Architectural Layers
1. **Structural Code Graph (`Layer 1`)**: Fast AST symbol parser (functions, classes, files, signatures) and dependency DAG (`CALLS`, `IMPORTS`, `INHERITS`).
2. **Cognitive Brain (`Layer 2`)**: Trace recorder linking sessions and failures to fixes and rules (`CO_MODIFIED_WITH`, `FAILED_ON`, `FIXED_BY`, `APPLIES_TO`).
3. **Hebbian Evolution**: Reinforcement on success ($\alpha=0.15$), attenuation on failure ($\beta=0.20$), dynamic half-life decay, and pruning.
4. **Token Compression**: Personalized PageRank (PPR) maps fitting large repositories into token budgets.
5. **Universal Connectors**: Native MCP tools (`search_brain`, `get_context_map`, `record_trace`, `suggest_fixes`) + CLI workbench (`sevolve brain ...`).
