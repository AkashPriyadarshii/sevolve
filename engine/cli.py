"""sevolve CLI.

Usage:
    sevolve evolve skill --name my-skill [--iterations 3] [--ci]
    sevolve artifacts                          # list versioned artifacts
    sevolve artifact-add skill --name s --file s.md
    sevolve ingest --file transcript.jsonl     # ingest execution trace
    sevolve promote --artifact skill/s --report report.md
    sevolve doctor                             # inspect system & tools
    sevolve seed-report                        # expand seed eval set
"""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path

from .artifact import ArtifactStore
from .executor import ClaudeClient
from .loop import evolve_artifact


def get_client() -> ClaudeClient | None:
    return ClaudeClient() if shutil.which("claude") else None


def _load_eval_set(path: str) -> dict:
    from evals.generator import expand_seed

    p = Path(path)
    if not p.exists():
        default = Path(__file__).resolve().parent.parent / "evals" / "seed.json"
        if p.name == "seed.json" and default.exists():
            p = default
        else:
            print(f"eval set not found: {path}", file=sys.stderr)
            sys.exit(1)
    return expand_seed(p)


def cmd_evolve(args) -> int:
    store = ArtifactStore(args.root)
    artifact = store.get(args.kind, args.name)
    if artifact is None:
        print(f"artifact {args.kind}/{args.name} not found; create it first (sevolve artifact-add)", file=sys.stderr)
        return 1
    eval_set = _load_eval_set(args.evals)
    client = get_client()
    ctx = {
        "client": client,
        "ci": args.ci,
        "max_size": args.max_size,
    }
    if client is None:
        print(
            "WARNING: no judge/optimizer client configured — running offline "
            "(traces + graders only). Set CLIENT or ensure 'claude' is on PATH.",
            file=sys.stderr,
        )
    from .report import write

    prev = artifact.get("score")
    result = evolve_artifact(
        store,
        artifact,
        eval_set,
        ctx,
        iterations=args.iterations,
        threshold=args.threshold,
    )
    path = write(result, prev, Path(args.root).parent / "report")
    print(f"report: {path}")
    print(f"promoted={result['promoted']} best_score={result['best_score']}")
    return 0


def cmd_artifacts(args) -> int:
    store = ArtifactStore(args.root)
    items = store.list()
    if not items:
        print("No artifacts found.")
        return 0
    for a in items:
        score_str = f"{a['score']:.3f}" if a["score"] is not None else "none"
        print(f"{a['kind']:9} {a['id']:20} v{a['version']} {a['status']:11} score={score_str}")
    return 0


def cmd_artifact_add(args) -> int:
    store = ArtifactStore(args.root)
    content = args.content
    if not content and args.file:
        content = Path(args.file).read_text(encoding="utf-8")
    if not content and not sys.stdin.isatty():
        content = sys.stdin.read()
    if not content or not content.strip():
        print("no content provided (use --content, --file, or stdin)", file=sys.stderr)
        return 1
    store.create(args.kind, args.name, content)
    print(f"created {args.kind}/{args.name} v1")
    return 0


def cmd_ingest(args) -> int:
    from .ingest import ingest_file

    try:
        tids = ingest_file(args.file, traces_dir=args.traces_dir)
        print(f"ingested {len(tids)} trace(s) from {args.file}: {', '.join(tids[:5])}{'...' if len(tids) > 5 else ''}")
        return 0
    except Exception as e:
        print(f"ingestion error: {e}", file=sys.stderr)
        return 1


def cmd_promote(args) -> int:
    from .promote import promote_artifact

    ok, msg = promote_artifact(
        args.artifact,
        args.report,
        artifacts_dir=args.root,
        base=args.base,
    )
    if ok:
        print(f"PR created: {msg}")
        return 0
    else:
        print(f"Promotion failed: {msg}", file=sys.stderr)
        return 1


def cmd_doctor(args) -> int:
    store = ArtifactStore(args.root)
    artifacts = store.list()
    traces_path = Path("traces")
    traces_count = len(list(traces_path.glob("*.jsonl"))) if traces_path.exists() else 0

    print("sevolve doctor - system status:")
    print(f"  claude CLI on PATH : {'yes' if shutil.which('claude') else 'no (offline mode)'}")
    print(f"  gh CLI on PATH     : {'yes' if shutil.which('gh') else 'no'}")
    print(f"  git on PATH        : {'yes' if shutil.which('git') else 'no'}")
    print(f"  artifact store     : {args.root} ({len(artifacts)} artifact(s))")
    print(f"  traces directory   : traces/ ({traces_count} trace file(s))")
    return 0


def cmd_seed_report(args) -> int:
    from evals.generator import expand_seed

    seed_path = Path(args.seed) if args.seed else Path(__file__).resolve().parent.parent / "evals" / "seed.json"
    data = expand_seed(seed_path)
    for task in data["tasks"]:
        task["_graders"] = {k: getattr(v, "__name__", "grader") for k, v in task["_graders"].items()}
    text = json.dumps(data, indent=2)
    if args.out:
        Path(args.out).write_text(text, encoding="utf-8")
        print(f"wrote seed report to {args.out}")
    else:
        sys.stdout.write(text + "\n")
    return 0


def main() -> None:
    ap = argparse.ArgumentParser(prog="sevolve", description="Self-evolving harness for LLM agents")
    ap.add_argument("--root", default="artifacts", help="artifact store root (default: artifacts)")
    sub = ap.add_subparsers(dest="cmd", required=True)

    ev = sub.add_parser("evolve", help="evolve an artifact")
    ev.add_argument("kind", choices=["skill", "prompt", "tool_desc", "rule"])
    ev.add_argument("--name", required=True)
    ev.add_argument("--iterations", type=int, default=3)
    ev.add_argument("--threshold", type=float, default=0.85)
    ev.add_argument("--evals", default="evals/seed.json")
    ev.add_argument("--max-size", type=int, default=16_000)
    ev.add_argument("--ci", action="store_true", help="skip human approval; NEVER skips mechanical gates")
    ev.set_defaults(func=cmd_evolve)

    aa = sub.add_parser("artifact-add", help="create a v1 artifact")
    aa.add_argument("kind", choices=["skill", "prompt", "tool_desc", "rule"])
    aa.add_argument("--name", required=True)
    aa.add_argument("--content", default="")
    aa.add_argument("--file", default="")
    aa.set_defaults(func=cmd_artifact_add)

    al = sub.add_parser("artifacts", help="list artifacts")
    al.set_defaults(func=cmd_artifacts)

    ing = sub.add_parser("ingest", help="ingest execution transcript into traces")
    ing.add_argument("--file", required=True, help="path to Claude transcript or JSONL trace")
    ing.add_argument("--traces-dir", default="traces", help="target traces directory")
    ing.set_defaults(func=cmd_ingest)

    prm = sub.add_parser("promote", help="promote artifact via git branch & gh PR")
    prm.add_argument("--artifact", required=True, help="kind/name e.g. skill/concise-summary")
    prm.add_argument("--report", required=True, help="path to report markdown")
    prm.add_argument("--base", default="master", help="base branch")
    prm.set_defaults(func=cmd_promote)

    doc = sub.add_parser("doctor", help="inspect environment, CLI tools, and traces")
    doc.set_defaults(func=cmd_doctor)

    sr = sub.add_parser("seed-report", help="expand seed eval set to JSON")
    sr.add_argument("--seed", default="", help="path to seed.json")
    sr.add_argument("--out", default="")
    sr.set_defaults(func=cmd_seed_report)

    # Brain subcommand group
    br = sub.add_parser("brain", help="Self-evolving code graph and cognitive brain commands")
    br_sub = br.add_subparsers(dest="brain_cmd", required=True)

    br_scan = br_sub.add_parser("scan", help="Scan Python AST symbols and dependencies into SQLite")
    br_scan.add_argument("dir", nargs="?", default=".", help="Directory to scan (default: .)")
    br_scan.add_argument("--db", default=".sevolve/brain.db", help="SQLite brain DB path")
    br_scan.set_defaults(func=lambda a: _call_brain("cmd_brain_scan", a))

    br_query = br_sub.add_parser("query", help="Hybrid FTS5 + graph search across symbols, rules, and fixes")
    br_query.add_argument("query", help="Search query")
    br_query.add_argument("--limit", type=int, default=10)
    br_query.add_argument("--db", default=".sevolve/brain.db")
    br_query.set_defaults(func=lambda a: _call_brain("cmd_brain_query", a))

    br_map = br_sub.add_parser("map", help="Get token-budgeted PageRank code context map")
    br_map.add_argument("file_path", help="Seed file path")
    br_map.add_argument("--tokens", type=int, default=1500)
    br_map.add_argument("--db", default=".sevolve/brain.db")
    br_map.set_defaults(func=lambda a: _call_brain("cmd_brain_map", a))

    br_sync = br_sub.add_parser("sync", help="Bidirectional sync with Obsidian Markdown vault")
    br_sync.add_argument("--vault", default=".sevolve/vault", help="Obsidian vault directory")
    br_sync.add_argument("--direction", choices=["export", "import"], default="export")
    br_sync.add_argument("--db", default=".sevolve/brain.db")
    br_sync.set_defaults(func=lambda a: _call_brain("cmd_brain_sync", a))

    br_prune = br_sub.add_parser("prune", help="Apply Hebbian decay and prune dead edges")
    br_prune.add_argument("--half-life", type=float, default=7.0)
    br_prune.add_argument("--threshold", type=float, default=0.05)
    br_prune.add_argument("--db", default=".sevolve/brain.db")
    br_prune.set_defaults(func=lambda a: _call_brain("cmd_brain_prune", a))

    br_mcp = br_sub.add_parser("mcp", help="Run stdio JSON-RPC MCP server for AI coding agents")
    br_mcp.add_argument("--db", default=".sevolve/brain.db", help="SQLite brain DB path")
    br_mcp.set_defaults(func=lambda a: _call_brain("cmd_brain_mcp", a))

    args = ap.parse_args()
    sys.exit(args.func(args))


def _call_brain(fn_name: str, args: argparse.Namespace) -> int:
    from .brain import cli as brain_cli
    fn = getattr(brain_cli, fn_name)
    return fn(args)


if __name__ == "__main__":
    main()
