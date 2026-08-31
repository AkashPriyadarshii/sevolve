# STATE - sevolve

Updated 2026-08-31. One source of truth for where the project stands.

## Version
**0.1.1** - finalized. 32 hermetic tests pass (0.39s), full CLI suite (`evolve`, `artifacts`, `artifact-add`, `ingest`, `promote`, `doctor`, `seed-report`), site live on GitHub Pages.

## Pipeline status
| Phase | Status |
|-------|--------|
| P0 scaffold (git, pyproject, LICENSE, README) | done |
| P1 artifact/trace/executor | done |
| P2 graders + judge + seed evals | done |
| P3 optimizer + gates + loop + report + CLI | done |
| P4 hermetic tests (18->32 pass) | done |
| P5 real-session traces (ingest) + PR promote + doctor | **done** |

## Capabilities
- Ingestion: parses Claude Code session JSONL and generic traces into `Trace` models.
- Evolution: GEPA reflect-and-propose on execution traces.
- Gates: mechanical byte size limit, regression hold check, and human approval / `--ci`.
- Promotion: automated Git branch + GitHub PR creation via `gh`.
- Graders: exact match, substring contains, length within bounds, regex match.
- Robustness: code-fence tolerant JSON decoding (` ```json `), zero read side-effects.
