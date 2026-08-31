# DESIGN — sevolve

## System Architecture

```
Agent Query (MCP / CLI) ──> engine/brain/mcp.py
                                   │
  ┌────────────────────────────────┴────────────────────────────────┐
  ▼                                                                 ▼
Layer 1: Structural Code Graph                     Layer 2: Cognitive Brain
(engine/brain/parser.py)                          (engine/brain/hebbian.py)
- AST symbol extraction (Python ast)              - Trace ingestion & failure linking
- CALLS / IMPORTS / INHERITS DAG                  - Hebbian edge weight reinforcement
- Token-budgeted PageRank (graph.py)              - Dynamic half-life decay & pruning
  │                                                                 │
  └────────────────────────────────┬────────────────────────────────┘
                                   ▼
              Storage Engine (engine/brain/db.py)
              - SQLite WAL mode + FTS5 trigram search
              - Recursive SQL CTE multi-hop graph walks (<1ms)
              - Bi-directional Markdown / Obsidian export (vault.py)
```

## Key Decisions

1. **Pure Standard Library Runtime**: Uses Python's built-in `sqlite3`, `ast`, `json`, `re`, and `argparse`. Zero external packages needed.
2. **SQLite WAL + FTS5 as Graph & Search Backend**: Graph edges stored in adjacency tables with index scans and recursive SQL CTEs, giving sub-millisecond graph traversals without running a separate graph database daemon.
3. **Dual-Layer Separation**: Structural AST code facts remain strictly deterministic; behavioral associations (co-modified files, failure causes, rule applicability) evolve continuously from real agent traces.
4. **Hebbian Reinforcement with Compaction**: Edges strengthen on task success, attenuate on failure, decay over time, and prune dead links to keep storage under <5MB.
5. **Universal JSON-RPC Stdio MCP Server**: Allows Claude Code, Cursor, OpenClaw, Codex, Windsurf, and Antigravity to connect without code changes.
6. **Bi-directional Obsidian Vault**: All nodes export to clean Markdown files with `[[WikiLinks]]` for human visualization in Obsidian.

## Module Layout (`engine/brain/`)

| Module | Purpose |
|---|---|
| `engine/brain/db.py` | SQLite connection manager, WAL mode, schema migrations, FTS5 table setup. |
| `engine/brain/parser.py` | Fast AST symbol and reference parser (classes, functions, calls, imports). |
| `engine/brain/graph.py` | Node/Edge CRUD, recursive CTE graph walks, Personalized PageRank. |
| `engine/brain/hebbian.py` | Hebbian edge reinforcement, attenuation, half-life decay, and pruning. |
| `engine/brain/mcp.py` | Stdio JSON-RPC 2.0 MCP server for coding agents. |
| `engine/brain/vault.py` | Bidirectional export/import between SQLite and Obsidian `.sevolve/vault/*.md`. |
| `engine/brain/cli.py` | Subcommands for `sevolve brain scan`, `query`, `map`, `sync`, `prune`. |

## Safety & Performance Invariants
- Query latency under 5ms.
- Memory footprint under 5MB RAM.
- 100% hermetic offline testing.
- Non-destructive passive code parsing.
