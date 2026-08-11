# AGENTS.md — sevolve

Rules for any agent working in this repo. Same brain as the user's global contract — shorter, repo-specific.

## Hard rules
- **Grader + judge run blind and separate** — never see the proposed diff. Reward-hacking defense.
- **Promote only on real improvement** — held-out score must rise. Never churn redundant versions.
- **`--ci` overrides human approval, never the mechanical gates.**
- **Evaluator sits outside the evolution loop.**
- **All tests hermetic** — no network, no API key. Run `python -m pytest -q` locally, always, before commit.

## Touch map
| Area | Rule |
|------|------|
| `engine/` | stdlib only. No new deps. Small modules, one job each. |
| `evals/` | seed tasks + generator. Adding a task is adding a case. |
| `traces/` | captured JSONL. Data, not code — don't edit by hand. |
| `artifacts/` | versioned content + meta.jsonl. Git is the store. |
| `site/` | static HTML, zero build. `site/index.html` must stay committed (Pages deploy archives it). |
| `docs/` | keep terse. Design changes land here first. |

## Workflow
1. Understand first (read the flow, not the file list).
2. Change engine → hermetic test → local full suite green.
3. Doc the change (CHANGELOG at minimum).
4. Commit conventional, push. GitHub via `gh`, never raw curl.

## Current status
P0-P4 done (v0.1.0, 18 tests green, site deploys). P5 pending: real-session trace hooks + PR promote + demo.
