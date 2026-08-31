# ARCHITECTURE — sevolve

## System Boundaries & Layers

`sevolve` operates as a **Dual-Layer Self-Evolving Code Graph & Cognitive Brain** built on standard library SQLite (WAL mode + FTS5 trigram indexing).

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

## 1. Graph Data Models

### Node Taxonomy
- **`SymbolNode` (`sym:`)**: Functions, classes, modules, files, methods, interfaces.
  - Attributes: `name`, `file_path`, `line_range`, `signature`, `docstring`, `content_hash`.
- **`RuleNode` (`rule:`)**: Project rules, architectural constraints, prompt lessons.
  - Attributes: `name`, `content`, `severity`, `scope_pattern`.
- **`TraceNode` (`trace:`)**: Execution episodes, prompts, tool sequences, final outcomes.
  - Attributes: `session_id`, `prompt`, `outcome` (`ok` / `fail`), `timestamp`, `cost`.
- **`FailureNode` (`fail:`)**: Stack traces, exceptions, test/lint failures.
  - Attributes: `error_type`, `error_message`, `stack_frames`, `hash`.
- **`FixNode` (`fix:`)**: Code patches, diffs, rationale that resolved a failure.
  - Attributes: `patch_diff`, `explanation`, `author_type`.
- **`TaskNode` (`task:`)**: Feature specs, user intents, issues.
  - Attributes: `goal`, `status`, `created_at`.

### Edge Taxonomy
- **Structural Edges (Deterministic AST)**:
  - `CALLS`: Function/Method $\to$ Function/Method
  - `IMPORTS`: File/Module $\to$ File/Module/Symbol
  - `INHERITS`: Class $\to$ Class
  - `DEFINED_IN`: Symbol $\to$ File
- **Cognitive & Behavioral Edges (Evolving)**:
  - `CO_MODIFIED_WITH`: Symbols frequently edited together in sessions.
  - `FAILED_ON`: `FailureNode` $\to$ `SymbolNode`
  - `FIXED_BY`: `FailureNode` $\to$ `FixNode` $\to$ `SymbolNode`
  - `APPLIES_TO`: `RuleNode` $\to$ `SymbolNode` / `File` / `Task`
  - `RECALLED_WITH`: Associative co-retrieval link between nodes.

---

## 2. Hebbian Evolution & Compaction Mechanics

1. **Success Reinforcement**:
   When an agent session completes successfully, active edges strengthen:
   $$W_{u,v}^{(t+1)} = \min(1.0, \; W_{u,v}^{(t)} + \alpha \cdot (1.0 - W_{u,v}^{(t)})) \quad (\alpha = 0.15)$$

2. **Failure Attenuation**:
   When a failure occurs, the path weight decreases:
   $$W_{u,v}^{(t+1)} = \max(0.0, \; W_{u,v}^{(t)} - \beta \cdot W_{u,v}^{(t)}) \quad (\beta = 0.20)$$

3. **Temporal Decay**:
   Unused behavioral edges decay over time:
   $$W_{u,v}(t) = W_{u,v}(t_0) \cdot e^{-\lambda (t - t_0)}$$

4. **Compaction & Pruning**:
   - Edges with $W < 0.05$ are pruned during compaction.
   - Repeated trace patterns consolidate into permanent `RuleNode` + `FixNode` pairs.

---

## 3. Storage & Traversal Engine

- **Storage**: Single `.sevolve/brain.db` with SQLite WAL mode and FTS5.
- **Graph Traversal**: Sub-millisecond recursive SQL Common Table Expressions (CTEs) traversing multi-hop neighborhoods with distance and weight attenuation.
- **Personalized PageRank**: Computes localized relevance vectors seeded on active files to fit the most relevant context into strict token limits.
- **Obsidian Vault Sync**: Bidirectional sync between SQLite and `.sevolve/vault/*.md` files with standard YAML frontmatter and `[[WikiLinks]]`.

---

## 4. Universal Interoperability

- **Stdio MCP Server**: Native JSON-RPC 2.0 interface (`search_brain`, `get_context_map`, `query_codegraph`, `record_trace`, `suggest_fixes`).
- **CLI Interface**: `sevolve brain scan`, `sevolve brain query`, `sevolve brain map`, `sevolve brain sync`, `sevolve brain prune`.
- **Markdown / Obsidian**: Open `.sevolve/vault/` directly in Obsidian to inspect interactive graph visualizations.

---

## Non-Goals
- No external heavy graph DBs (Neo4j, Memgraph, Dgraph).
- No GPU / PyTorch dependencies.
- No network daemons or background resource hogs. Zero budget ($0), stdlib-only.
