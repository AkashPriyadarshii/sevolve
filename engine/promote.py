#!/usr/bin/env python3
"""PR Promote — promote best artifact variant via gh PR.

Usage: python engine/promote.py --artifact skill/concise-summary --report report/report-*.md
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Any


def run_cmd(cmd: list[str], cwd: Path | None = None) -> tuple[int, str, str]:
    proc = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
    return proc.returncode, proc.stdout, proc.stderr


def parse_report(report_path: Path) -> dict[str, Any] | None:
    """Extract promoted artifact info from report markdown."""
    content = report_path.read_text(encoding="utf-8")
    data = {}
    m = re.search(r"promoted=(true|false)\s+best_score=([\d.]+)", content)
    if m:
        data["promoted"] = m.group(1) == "true"
        data["best_score"] = float(m.group(2))
    m = re.search(r"Artifact:\s*(\w+)/(\S+)", content)
    if m:
        data["kind"] = m.group(1)
        data["id"] = m.group(2)
    return data if data else None


def get_artifact_content(kind: str, aid: str, artifacts_dir: Path) -> str | None:
    """Get latest version content from artifact store."""
    artifact_dir = artifacts_dir / kind / aid
    if not artifact_dir.exists():
        return None
    versions = sorted(artifact_dir.glob("v*.txt"))
    if not versions:
        return None
    return versions[-1].read_text(encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser(prog="promote", description="Promote artifact via gh PR")
    ap.add_argument("--artifact", required=True, help="kind/name e.g. skill/concise-summary")
    ap.add_argument("--report", required=True, help="path to report file")
    ap.add_argument("--artifacts-dir", default="artifacts", help="artifact store root")
    ap.add_argument("--base", default="master", help="base branch")
    args = ap.parse_args()

    report_path = Path(args.report)
    if not report_path.exists():
        print(f"report not found: {report_path}", file=sys.stderr)
        return 1

    report_data = parse_report(report_path)
    if not report_data or not report_data.get("promoted"):
        print("report indicates no promotion (not promoted or no best_score)")
        return 0

    kind, aid = args.artifact.split("/", 1)
    content = get_artifact_content(kind, aid, Path(args.artifacts_dir))
    if not content:
        print(f"artifact content not found: {kind}/{aid}", file=sys.stderr)
        return 1

    branch = f"promote/{kind}/{aid}"
    rc, out, err = run_cmd(["git", "checkout", "-b", branch])
    if rc != 0:
        run_cmd(["git", "checkout", branch])
        run_cmd(["git", "reset", "--hard", args.base])

    artifact_dir = Path(args.artifacts_dir) / kind / aid
    latest = sorted(artifact_dir.glob("v*.txt"))[-1]
    latest.write_text(content, encoding="utf-8")

    rc, out, err = run_cmd(["git", "add", str(latest)])
    if rc != 0:
        print(f"git add failed: {err}", file=sys.stderr)
        return 1

    msg = f"promote: {kind}/{aid} held-out score {report_data['best_score']:.2f}\n\nReport: {report_path}"
    rc, out, err = run_cmd(["git", "commit", "-m", msg])
    if rc != 0:
        print(f"git commit failed: {err}", file=sys.stderr)
        return 1

    rc, out, err = run_cmd(["git", "push", "-u", "origin", branch])
    if rc != 0:
        print(f"git push failed: {err}", file=sys.stderr)
        return 1

    rc, out, err = run_cmd([
        "gh", "pr", "create",
        "--base", args.base,
        "--head", branch,
        "--title", f"promote: {kind}/{aid} ({report_data['best_score']:.2f})",
        "--body", f"Promoted via sevolve evolution loop.\n\nReport: {report_path}\n\nHeld-out score: {report_data['best_score']:.2f}"
    ])
    if rc != 0:
        print(f"gh pr create failed: {err}", file=sys.stderr)
        return 1

    print(f"PR created: {out.strip()}")
    return 0


if __name__ == "__main__":
    sys.exit(main())