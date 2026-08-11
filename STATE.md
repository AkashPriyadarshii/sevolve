# STATE — sevolve

Updated 2026-08-12. One source of truth for where the project stands.

## Version
**0.1.0** — finalized. `master` synced with origin, 18 hermetic tests pass, site live on GitHub Pages.

## Pipeline status
| Phase | Status |
|-------|--------|
| P0 scaffold (git, pyproject, LICENSE, README) | done |
| P1 artifact/trace/executor | done |
| P2 graders + judge + seed evals | done |
| P3 optimizer + gates + loop + report + CLI | done |
| P4 hermetic tests (15→18 pass) | done |
| P5 real-session traces (hooks) + PR promote + demo | **pending — next** |

## Known limitations
- Executor hardcoded `claude -p` + sonnet. Configurable command = next.
- Judge/optimizer client is a hook point, not a wired provider.
- Seed evals: 2 tasks, concise-summary domain.

## Deploy
GitHub Pages workflow `.github/workflows/deploy.yml`, Actions source. Root causes fixed this session: Pages not enabled (now enabled, build_type=workflow), `site/index.html` was gitignored (un-ignored, committed).

## Uncommitted
`traces/20260811T192837.jsonl` — session trace data (captured, not yet pushed).
