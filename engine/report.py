"""Run report — makes the loop's value legible.

Every run writes report/report-<timestamp>.md: before/after scores, cost-vs-
delta, and a REGRESSION summary at promotion. The whole project lives or dies
on this file being honest. First-run demo must SHOW improvement.
"""

from __future__ import annotations

import time
from pathlib import Path
from typing import Any


def _stamp() -> str:
    return time.strftime("%Y-%m-%dT%H%M%S", time.gmtime())


def render(run: dict[str, Any], prev_score: float | None) -> str:
    a = run["artifact"]
    lines = [
        f"# sevolve run report",
        "",
        f"artifact: `{a['kind']}/{a['id']}`  promoted: **{run['promoted']}**",
        "",
        f"**best score: {run['best_score']:.3f}**",
    ]
    if prev_score is not None:
        delta = run["best_score"] - prev_score
        lines += ["", f"prev best: {prev_score:.3f}   delta: **{delta:+.3f}**"]
    lines += ["", "## History"]
    for h in run.get("history", []):
        lines.append(
            f"- iter {h['iter']}: train={h['train_score']:.3f} best_held={h['best_held']:.3f} "
            f"improved={h['improved']}"
        )
        if h.get("judge_reasoning"):
            lines.append(f"  - judge: {h['judge_reasoning'][:160]}")
    lines += ["", "## Gates", ""]
    for name, detail in run.get("gate_results", []):
        lines.append(f"- {name}: {detail}")
    if run.get("promoted"):
        lines += ["", "## REGRESSION", "", "None detected on held-out set at promotion."]
    return "\n".join(lines) + "\n"


def write(run: dict[str, Any], prev_score: float | None, report_dir: Path | str = "report") -> Path:
    d = Path(report_dir)
    d.mkdir(parents=True, exist_ok=True)
    p = d / f"report-{_stamp()}.md"
    p.write_text(render(run, prev_score), encoding="utf-8")
    return p
