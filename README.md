# sevolve

[![CI](https://github.com/AkashPriyadarshii/sevolve/actions/workflows/deploy.yml/badge.svg)](https://github.com/AkashPriyadarshii/sevolve/actions)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10+-brightgreen.svg)](https://python.org)
[![Tests: 32 Green](https://img.shields.io/badge/Tests-32%20Hermetic-success.svg)](https://github.com/AkashPriyadarshii/sevolve)
[![Zero GPU](https://img.shields.io/badge/GPU-0MB%20Req-orange.svg)](https://github.com/AkashPriyadarshii/sevolve)

**Self-evolving harness for LLM agents.** Evolve the machine around the model: skills, system prompts, tool descriptions, and agent rules directly from real execution traces.

The model weights stay fixed. The harness gets smarter.

```
sample task ---> run with current artifact ---> capture trace ---> grade (blind)
     ^                                                                 │
     │                                                                 v
promote (gates + PR) <--- pick best on held-out <--- optimizer reflects on trace
```

---

## Why sevolve?

Fine-tuning model weights is slow, expensive, and gets wiped out whenever foundation models update. Real agent performance in production depends on the **machinery around the model**: prompt constraints, skill definitions (`SKILL.md`), tool parameters, and error recovery logic.

`sevolve` optimizes that machinery automatically from real terminal failures.

| Feature | `sevolve` | DSPy / TextGrad | PromptBreeder / RL |
|---|---|---|---|
| **Runtime Overhead** | **Zero deps (Python stdlib)** | Heavy frameworks, PyTorch | Heavy compute / GPU |
| **Artifact Format** | **Plain Markdown & JSON files** | Proprietary Python classes | Opaque weight/search states |
| **Grading Safety** | **Blind Grader & Judge** | Judge sees candidate prompt | Prone to reward hacking |
| **Promotion Path** | **Automated Git Branch & GitHub PR** | Ephemeral memory buffer | Opaque tensors |
| **Guardrails** | **Byte budget & regression gates** | Manual inspection | None (prompt explosion) |

---

## Key Features

1. **In-Situ File Mutation:** Optimizes files that already exist in your repository (`SKILL.md`, `AGENTS.md`, `.cursorrules`, MCP tool schemas).
2. **Trace-Driven Reflection:** Ingests real Claude Code, OpenClaw, and terminal execution logs to understand exactly where tasks failed.
3. **Reward-Hacking Immunity:** Evaluators and LLM judges **never see the proposed prompt diff**, only task execution outputs against fixed rubrics.
4. **Mechanical Guardrails:** Every proposed change must pass hard byte-size caps and held-out regression sets before promotion.
5. **Git-Native Promotion:** Automatically cuts a branch, commits the versioned artifact, and opens a GitHub Pull Request via `gh`.

---

## Quickstart

### 1. Installation

```bash
git clone https://github.com/AkashPriyadarshii/sevolve.git
cd sevolve
pip install -e .
```

### 2. Check Environment

```bash
sevolve doctor
```

```text
sevolve doctor - system status:
  claude CLI on PATH : yes
  gh CLI on PATH     : yes
  git on PATH        : yes
  artifact store     : artifacts (1 artifact(s))
  traces directory   : traces/ (20 trace file(s))
```

### 3. Ingest Real Session Logs

Capture real execution logs from Claude Code or your agent harness into structured traces:

```bash
sevolve ingest --file ~/.claude/projects/my-project/session.jsonl
```

### 4. Add an Artifact & Evolve

Create a versioned skill and evolve it against an evaluation suite:

```bash
# Register an initial skill
sevolve artifact-add skill --name concise-summary --file my-skill.md

# Run the evolution loop
sevolve evolve skill --name concise-summary --iterations 5 --ci
```

### 5. Inspect and Promote

```bash
# List all tracked artifacts and scores
sevolve artifacts

# Open a GitHub PR with the promoted variant
sevolve promote --artifact skill/concise-summary --report report/report-latest.md
```

---

## CLI Reference

| Command | Arguments | Description |
|---|---|---|
| `sevolve evolve <kind>` | `--name <id>` `[--iterations N]` `[--ci]` | Runs reflection loop over train task, validates on held-out task |
| `sevolve ingest` | `--file <path>` `[--traces-dir <dir>]` | Ingests Claude Code session JSONL or generic trace logs |
| `sevolve artifacts` | `[--root <dir>]` | Lists all versioned artifacts, scores, and promotion states |
| `sevolve artifact-add <kind>` | `--name <id>` `[--file <path> \| --content <str>]` | Registers a new v1 artifact into the store |
| `sevolve promote` | `--artifact <kind>/<id>` `--report <path>` | Creates a git branch and opens a GitHub PR via `gh` |
| `sevolve doctor` | `[--root <dir>]` | Checks environment, CLIs on PATH, store count, and trace health |
| `sevolve seed-report` | `[--out <file>]` | Expands declarative seed eval tasks into formatted JSON |

---

## Architecture & Layout

```text
engine/
├── artifact.py       # Versioned filesystem store with single-pass metadata writes
├── cli.py            # CLI entrypoint (evolve, artifacts, ingest, promote, doctor)
├── executor.py       # Subprocess runner & ClaudeClient provider adapter
├── gate.py           # Mechanical gates (size limits, regression holds, human approval)
├── grader.py         # Deterministic checks (exact, contains, regex, length bounds)
├── ingest.py         # Transcript parser for Claude Code & JSONL traces
├── judge.py          # Blind LLM-as-judge rubric evaluator with JSON code fence parser
├── loop.py           # Core evolution loop (train reflection + held-out promotion)
├── optimizer.py      # GEPA reflect-and-propose mutation engine
├── promote.py        # Automated Git branch and GitHub PR promotion
├── report.py         # Markdown run reports with score delta tables
└── trace.py          # Execution trace capture, serialization, and formatting
```

---

## Testing

All tests are hermetic, run locally without network requests or API keys, and complete in under 0.5s:

```bash
python -m pytest -v
```

```text
============================= 32 passed in 0.39s =============================
```

---

## License

MIT License. Created by [Akash Priyadarshi](https://github.com/AkashPriyadarshii).
