# sevolve

Self-evolving harness for LLM agents. **Evolve the machine around the model — skills, prompts, tool descriptions, rules — from real execution traces.** The model stays fixed. The harness learns.

No GPU. No weight training. No closed services. MIT. Runs on an API key.

## The loop

```
sample task ──> run with current artifact ──> capture trace ──> grade (blind)
        ^                                                        │
        │                                                        v
   promote (gates + PR) <── pick best on held-out <── optimizer reflects on trace
```

- **Trace** — what actually happened: task, tool calls, failures, output.
- **Blind grader** — hard checks + LLM-as-judge, running in a separate read-only process. Never sees the proposed improvement. No reward hacking.
- **Optimizer** — reads the trace, explains *why* it failed, proposes candidate variants.
- **Gates** — size limits, regression set, tests, human review. `--ci` overrides human approval, never the gates.
- **Promote** — best variant on held-out data, version bump, PR.

## Install

```bash
pip install -e .
export ANTHROPIC_API_KEY=...
```

## Use

```bash
sevolve evolve skill --name my-skill --iterations 5
```

Reads real traces, proposes improved skill variants, gates them, opens a PR.

## Scope

Harness evolution only. **No weight training. No GPU.** If you want to fine-tune a model, this isn't the tool. If you want the machine around the model to get better at your tasks, it is.

## Layout

```
engine/     cli, artifact, trace, executor, grader, judge, optimizer, gate, report
evals/      seed task sets + generator
traces/     captured execution traces (JSONL)
artifacts/  versioned skills/prompts/rules + metadata
site/       marketing site (static HTML, zero build)
tests/      hermetic — no API key needed
```

## How it's built

7 small modules, stdlib-only runtime, tests that run locally with no network.
