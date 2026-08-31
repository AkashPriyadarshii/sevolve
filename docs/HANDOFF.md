# HANDOFF — sevolve

## What is sevolve
A zero-dependency, zero-GPU **Self-Evolving Code Graph & Cognitive Brain** for AI agents. Combines a structural AST code graph (functions, classes, calls, imports) with an evolving cognitive brain (traces, failures, fixes, rules) using Hebbian dynamics. Pure Python stdlib (`sqlite3` WAL + FTS5), <5ms query, <5MB RAM.

## Working Components
- **Brain Engine (`engine/brain/`)**: SQLite WAL storage, AST parser, Hebbian dynamics, PageRank token compression, stdio MCP server, Obsidian vault sync.
- **Trace Ingestion (`engine/ingest.py`)**: Parses Claude Code session transcripts and generic JSONL logs into `Trace` models.
- **Evaluation & Promotion (`engine/`)**: Blind grading, GEPA reflect-and-propose optimizer, mechanical size/regression gates, PR promoter.
- **CLI**: `sevolve brain scan|query|map|sync|prune`, `sevolve evolve|artifacts|ingest|promote|doctor`.
- **Tests**: 100% hermetic tests running in <0.4s with zero network dependencies.

## Key Files
- `engine/brain/db.py`: SQLite WAL schema and migrations.
- `engine/brain/parser.py`: AST symbol and dependency extraction.
- `engine/brain/graph.py`: Recursive SQL CTE graph walks and PageRank.
- `engine/brain/hebbian.py`: Edge reinforcement and decay mathematics.
- `engine/brain/mcp.py`: Universal stdio JSON-RPC 2.0 MCP server.
- `engine/brain/vault.py`: Markdown Obsidian `.sevolve/vault/` sync.
