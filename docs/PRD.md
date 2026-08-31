# PRD — sevolve

## Problem
Coding agents struggle with complex repositories:
1. **Context Blindness**: Flat file dumps exceed token limits or omit critical caller/callee relationships.
2. **Amnesia**: Agents repeat the same mistakes across sessions because they don't persist failure causes or co-modification patterns.
3. **Bloated Tooling**: Existing graph/memory tools require heavy background databases (Neo4j, Docker), high RAM, or closed vector services.

## Product
`sevolve` — a zero-dependency, zero-GPU **Self-Evolving Code Graph & Cognitive Brain**.
It parses the codebase into an AST structural graph (classes, functions, calls, imports), captures execution traces into a cognitive graph (rules, failures, fixes), evolves edge weights via Hebbian dynamics, and serves token-budgeted context to any agent via stdio MCP.

## Users
- AI coding agents and developers using Claude Code, Cursor, OpenClaw, Codex, Windsurf, or Antigravity.
- Developers wanting instant (<5ms) repository maps and persistent cross-session memory without running heavy servers.

## Scope (Locked)
- **In**: AST symbol extraction, SQLite WAL + FTS5 graph storage, Hebbian edge weight evolution, token-budgeted PageRank context maps, stdio MCP server, Obsidian Markdown vault sync, 100% hermetic tests.
- **Out**: External graph databases, GPU weight training, vector database servers, cloud lock-in.

## Success Criteria
1. Instant AST code graph indexing (<500ms for 10k LOC).
2. Sub-5ms query and multi-hop graph traversal.
3. Hebbian reinforcement updates edge weights from real execution traces.
4. Universal MCP server connects to Claude Code and Cursor out-of-the-box.
5. 100% hermetic tests pass locally. Zero third-party dependencies.
