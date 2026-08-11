# PRD — sevolve

## Problem
Agents plateau: humans manually patch prompts, skills, and rules after every failure. The improvements don't compound, aren't versioned, and aren't verified.

## Product
`sevolve` — an engine that captures execution traces, grades them blindly, reflects on why an artifact failed, proposes improved variants, gates them, and promotes the best on held-out data. The machine around the model evolves; the model stays fixed.

## Users
- FOSS developers building agents on Claude Code / any LLM CLI.
- Anyone who wants their skills/prompts to measurably improve from real use, not vibes.

## Scope (locked)
In: harness-level evolution — skills, prompts, tool descriptions, rules. Versioned. Trace-driven. Gated. MIT.
Out: weight training, fine-tuning, RL. No GPU. Never.

## Success criteria
1. Bad seed skill scores UP on held-out data after evolution (verified by hermetic test).
2. Regression set doesn't drop at promotion.
3. First run costs <$10 and shows a before/after report.
4. Anyone: `pip install -e .` + API key → `sevolve evolve skill --name my-skill`.

## Anti-goals
- No auto-approve without gates.
- No churn of redundant versions.
- No silently churning on a weak judge — capability warning instead.

## Out of scope (v1)
- Weight evolution, multi-agent topology evolution, environment generation.
