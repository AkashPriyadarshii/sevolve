# sevolve

[![CI](https://github.com/AkashPriyadarshii/sevolve/actions/workflows/deploy.yml/badge.svg)](https://github.com/AkashPriyadarshii/sevolve/actions)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10+-brightgreen.svg)](https://python.org)
[![Tests: 32 Green](https://img.shields.io/badge/Tests-32%20Hermetic-success.svg)](https://github.com/AkashPriyadarshii/sevolve)
[![Zero Dependencies](https://img.shields.io/badge/Dependencies-Stdlib%20Only-success.svg)](https://github.com/AkashPriyadarshii/sevolve)
[![Zero GPU](https://img.shields.io/badge/GPU-0MB%20Req-orange.svg)](https://github.com/AkashPriyadarshii/sevolve)

**Zero-dependency, zero-GPU Self-Evolving Code Graph & Cognitive Brain for AI agents.**

Plugs into **Claude Code, Cursor, OpenClaw, Codex, Windsurf, and Antigravity** via native stdio MCP, CLI, or bi-directional Obsidian Markdown vaults.

```
┌─────────────────────────────────────────────────────────────┐
│                     ANY CODING AGENT                        │
│      Claude Code · Cursor · OpenClaw · Codex · Antigravity  │
└───────────────┬───────────────────┬────────────────────┬────┘
                │ stdio MCP         │ CLI                │ File View
                ▼                   ▼                    ▼
  ┌───────────────────┐  ┌──────────────────┐  ┌───────────────────────┐
  │ Native MCP Server │  │ `sevolve brain`  │  │ Obsidian Markdown     │
  │ (JSON-RPC stdio)  │  │ CLI Subcommands  │  │ `.sevolve/vault/*.md` │
  └─────────┬─────────┘  └─────────┬────────┘  └───────────┬───────────┘
            └──────────────────────┼───────────────────────┘
                                   ▼
  ┌────────────────────────────────────────────────────────────────────┐
  │                      sevolve ENGINE                                │
  │  ┌──────────────────────────────────────────────────────────────┐  │
  │  │ Layer 1: Structural Code Graph (AST, Calls, Imports, Symbols)│  │
  │  ├──────────────────────────────────────────────────────────────┤  │
  │  │ Layer 2: Cognitive Brain (Traces, Failures, Fixes, Rules)    │  │
  │  ├──────────────────────────────────────────────────────────────┤  │
  │  │ Evolution: Hebbian edge reinforcement & dynamic decay        │  │
  │  ├──────────────────────────────────────────────────────────────┤  │
  │  │ Storage: SQLite WAL + FTS5 (Zero deps, <4MB RAM, <5ms query) │  │
  │  └──────────────────────────────────────────────────────────────┘  │
  └────────────────────────────────────────────────────────────────────┘
```

---

## Why sevolve?

Flat file dumps and brute-force grep waste tokens and lose critical caller/callee context. Heavy graph databases (Neo4j, Docker) require servers, high RAM, and complex configuration.

`sevolve` delivers a **dual-layer self-evolving brain** in pure Python standard library:
1. **Layer 1 (Structural Code Graph):** Extracts classes, functions, files, signatures, and call/import dependencies into a SQLite WAL graph. Token-budgeted PageRank code maps fit 10k LOC into ~250 tokens.
2. **Layer 2 (Cognitive Evolving Brain):** Ingests real execution traces. Links failing tasks to fixes and rules.
3. **Hebbian Evolution:** Successful paths strengthen ($\alpha=0.15$), failing paths attenuate ($\beta=0.20$), and unused edges decay over time.
4. **Universal Connectors:** Connects out-of-the-box to any agent via stdio MCP or CLI.

| Metric | `sevolve` | Neo4j / Graph RAG | Heavy Vector DBs |
|---|---|---|---|
| **Runtime Overhead** | **<5 MB RAM (Stdlib Python)** | >500 MB RAM + JVM/Docker | >300 MB RAM + Server |
| **Query Latency** | **<5ms (SQLite WAL + CTE)** | 50–200ms (Network) | 80–300ms (Embeddings) |
| **Dependencies** | **0 (Zero external deps)** | Heavy client drivers | PyTorch, Transformers, ONNX |
| **Storage Format** | **Single `.sevolve/brain.db`** | Complex binary cluster | Vector index blobs |
| **Human Readable** | **Obsidian Vault (`[[links]]`)** | Cypher queries only | Opaque floating point vectors |

---

## Quickstart

### 1. Installation

```bash
git clone https://github.com/AkashPriyadarshii/sevolve.git
cd sevolve
pip install -e .
```

### 2. Scan & Index Codebase

Index AST symbols, function signatures, and call dependencies into the local SQLite brain:

```bash
sevolve brain scan .
```

### 3. Query the Brain

```bash
# Search symbols, rules, and known fixes via hybrid FTS5 + Graph
sevolve brain query "trace parser"

# Print local symbol neighborhood with co-modified files
sevolve brain map engine/trace.py
```

### 4. Connect to Any Coding Agent via MCP

Add to your Claude Code / Cursor MCP configuration:

```json
{
  "mcpServers": {
    "sevolve": {
      "command": "python",
      "args": ["-m", "engine.brain.mcp"]
    }
  }
}
```

The agent gets 4 native tools:
- `search_brain(query, limit)`: Fast hybrid FTS5 + graph search.
- `get_context_map(files, token_budget)`: PageRank token-budgeted code map.
- `record_trace(session_id, prompt, actions, outcome)`: Ingests trace and updates Hebbian weights.
- `suggest_fixes(error_trace)`: Looks up `FailureNode → FIXED_BY → FixNode`.

### 5. Sync with Obsidian Vault

Export the graph into Markdown with `[[WikiLinks]]` to view interactively in Obsidian:

```bash
sevolve brain sync --vault .sevolve/vault
```

---

## CLI Reference

| Command | Arguments | Description |
|---|---|---|
| `sevolve brain scan` | `[dir]` | Parses AST symbols, signatures, and dependencies into SQLite |
| `sevolve brain query` | `<query>` `[--limit N]` | Hybrid FTS5 + graph search across symbols, rules, and fixes |
| `sevolve brain map` | `<file_path>` | Prints symbol neighborhood, callers, callees, and co-modified files |
| `sevolve brain sync` | `[--vault <dir>]` | Bidirectional sync with Obsidian Markdown vault (`[[links]]`) |
| `sevolve brain prune` | `[--threshold W]` | Applies Hebbian decay and prunes dead edges |
| `sevolve ingest` | `--file <path>` | Ingests Claude Code session transcripts or generic JSONL logs |
| `sevolve doctor` | `[--root <dir>]` | System diagnostics: SQLite WAL status, trace count, and tool health |

---

## Testing

All 32 tests are hermetic, run offline with zero network requests or API keys, and complete in <0.4s:

```bash
python -m pytest -v
```

---

## License

MIT License. Created by [Akash Priyadarshi](https://github.com/AkashPriyadarshii).
