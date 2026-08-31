# session-handoff — sevolve

Fast resume pointer for `sevolve`.

## Status
- v0.1.1 completed and tagged on GitHub.
- Architecture pivoted to **Self-Evolving Code Graph & Cognitive Brain** (`engine/brain/`).
- Markdown documentation updated across `README.md`, `AGENTS.md`, `CLAUDE.md`, `STATE.md`, `docs/`.

## Invariants to Preserve
- Pure Python stdlib (`sqlite3`, `ast`, `json`, `re`, `argparse`). Zero external packages.
- Sub-5ms query times, sub-5MB memory footprint.
- All tests hermetic (`python -m pytest -q`).
- Universal stdio JSON-RPC MCP server for Claude Code, Cursor, OpenClaw, Codex, Windsurf, and Antigravity.
