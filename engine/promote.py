#!/usr/bin/env python3
"""PR Promote — promote best artifact variant via gh PR.

Usage:
    python -m engine.promote --artifact skill/concise-summary --report report/report-*.md
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path
from typing import Any, Callable


def run_cmd(cmd: list[str], cwd: Path | None = None) -> tuple[int, str, str]:
    proc = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
    return proc.returncode, proc.stdout, proc.stderr


def parse_report(report_path: Path | str) -> dict[str, Any] | None:
    """Extract promoted artifact info from report markdown."""
    p = Path(report_path)
    if not p.exists():
        return None
    content = p.read_text(encoding="utf-8")
    data: dict[str, Any] = {}

    # Match artifact kind/id: e.g. "artifact: `skill/concise-summary`" or "Artifact: skill/concise-summary"
    m_art = re.search(r"artifact:\s*[`]?([a-zA-Z0-9_-]+)/([a-zA-Z0-9_.-]+)[`]?", content, re.IGNORECASE)
    if m_art:
        data["kind"] = m_art.group(1)
        data["id"] = m_art.group(2)

    # Match promoted status: e.g. "promoted: **True**" or "promoted=true"
    m_prom = re.search(r"promoted[:=]\s*(?:\*\*)?(true|false)(?:\*\*)?", content, re.IGNORECASE)
    if m_prom:
        data["promoted"] = m_prom.group(1).lower() == "true"

    # Match best score: e.g. "**best score: 0.950**" or "best_score=0.95"
    m_score = re.search(r"(?:best\s+score[:=]|best_score=)\s*(?:\*\*)?([\d.]+)(?:\*\*)?", content, re.IGNORECASE)
    if m_score:
        data["best_score"] = float(m_score.group(1))

    return data if ("kind" in data and "promoted" in data) else None


def get_artifact_content(kind: str, aid: str, artifacts_dir: Path | str) -> str | None:
    """Get latest version content from artifact store."""
    artifact_dir = Path(artifacts_dir) / kind / aid
    if not artifact_dir.exists():
        return None
    versions = sorted(artifact_dir.glob("v*.txt"))
    if not versions:
        return None
    return versions[-1].read_text(encoding="utf-8")


def promote_artifact(
    artifact_spec: str,
    report_path: Path | str,
    artifacts_dir: Path | str = "artifacts",
    base: str = "master",
    runner: Callable[[list[str]], tuple[int, str, str]] = run_cmd,
) -> tuple[bool, str]:
    """Promotes an artifact version via git branch and gh PR."""
    report_data = parse_report(report_path)
    if not report_data or not report_data.get("promoted"):
        return False, "report indicates artifact was not promoted"

    kind, aid = artifact_spec.split("/", 1) if "/" in artifact_spec else (report_data["kind"], report_data["id"])
    content = get_artifact_content(kind, aid, artifacts_dir)
    if not content:
        return False, f"artifact content not found: {kind}/{aid}"

    score = report_data.get("best_score", 1.0)
    branch = f"promote/{kind}/{aid}"
    rc, _, _ = runner(["git", "checkout", "-b", branch])
    if rc != 0:
        runner(["git", "checkout", branch])
        runner(["git", "reset", "--hard", base])

    artifact_file = Path(artifacts_dir) / kind / aid
    latest_files = sorted(artifact_file.glob("v*.txt"))
    if not latest_files:
        return False, "no version file to commit"

    rc, _, err = runner(["git", "add", str(latest_files[-1])])
    if rc != 0:
        return False, f"git add failed: {err}"

    msg = f"promote: {kind}/{aid} held-out score {score:.2f}\n\nReport: {report_path}"
    rc, _, err = runner(["git", "commit", "-m", msg])
    if rc != 0 and "nothing to commit" not in err.lower() and "clean" not in err.lower():
        return False, f"git commit failed: {err}"

    rc, _, err = runner(["git", "push", "-u", "origin", branch])
    if rc != 0:
        return False, f"git push failed: {err}"

    rc, out, err = runner([
        "gh", "pr", "create",
        "--base", base,
        "--head", branch,
        "--title", f"promote: {kind}/{aid} ({score:.2f})",
        "--body", f"Promoted via sevolve evolution loop.\n\nReport: {report_path}\n\nHeld-out score: {score:.2f}",
    ])
    if rc != 0:
        return False, f"gh pr create failed: {err}"

    return True, out.strip()


def main() -> int:
    ap = argparse.ArgumentParser(prog="promote", description="Promote artifact via gh PR")
    ap.add_argument("--artifact", required=True, help="kind/name e.g. skill/concise-summary")
    ap.add_argument("--report", required=True, help="path to report file")
    ap.add_argument("--artifacts-dir", default="artifacts", help="artifact store root")
    ap.add_argument("--base", default="master", help="base branch")
    args = ap.parse_args()

    ok, msg = promote_artifact(
        args.artifact,
        args.report,
        artifacts_dir=args.artifacts_dir,
        base=args.base,
    )
    if ok:
        print(f"PR created: {msg}")
        return 0
    else:
        print(f"Promotion failed: {msg}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())