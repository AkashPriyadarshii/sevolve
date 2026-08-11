# session-handoff — sevolve

How to resume this repo fast. Read STATE.md for status, this for what's next.

## Where it left off
v0.1.0 finalized. Deploy fixed (Pages enabled + gitignore bug). 18 tests green. Next is P5.

## Next task: P5 — real-session traces + PR promote + demo
1. **Hook config** — Claude Code `SessionEnd`/`Stop` hook dumps transcript to `traces/<ts>.jsonl`. Ship as `hookify` config or documented settings.json block. See `engine/trace.py` for the shape it must match.
2. **PR promote** — `promote` path: gates pass → create PR via `gh` (not raw curl) instead of local version bump only.
3. **Demo** — one artifact evolved end-to-end from a real trace, report in `report/`, before/after shown.
4. Optionally: cron scheduler that auto-runs `sevolve evolve` after sessions (this is the "fully autonomous" step).

## Verify before committing
- `python -m pytest -q` full suite green (hermetic, no network).
- Trace parser round-trips: captured transcript → valid Trace.
- PR path uses `gh`, never curl.

## Don't regress
- Blind grading (grader never sees diff).
- Promote only on held-out gain.
- `site/index.html` stays committed — Pages deploy archives it.
- Stdlib only in `engine/`.
