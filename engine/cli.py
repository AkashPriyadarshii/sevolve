"""sevolve CLI.

Usage:
    sevolve evolve skill --name my-skill [--iterations 3] [--ci]
    sevolve artifacts                          # list versioned artifacts
    sevolve seed-report                        # expand seed eval set
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .artifact import ArtifactStore
from .loop import evolve_artifact

# Judge + optimizer client: hook point for provider wiring. Offline default so
# the CLI runs without a key until a client is configured. Tests inject a
# scripted client instead.
CLIENT = None


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
        print(f"artifact {args.kind}/{args.name} not found; create it first "
              "(sevolve artifact-add)", file=sys.stderr)
        return 1
    eval_set = _load_eval_set(args.evals)
    ctx = {
        "client": CLIENT,
        "ci": args.ci,
        "max_size": args.max_size,
    }
    if CLIENT is None:
        print("WARNING: no judge/optimizer client configured — running offline "
              "(traces + graders only). Set CLIENT or pass a wired client.", file=sys.stderr)
    from .report import write
    prev = artifact.get("score")
    result = evolve_artifact(
        store, artifact, eval_set, ctx,
        iterations=args.iterations, threshold=args.threshold,
    )
    path = write(result, prev, Path(args.root).parent / "report")
    print(f"report: {path}")
    print(f"promoted={result['promoted']} best_score={result['best_score']}")
    return 0


def cmd_artifacts(args) -> int:
    store = ArtifactStore(args.root)
    for a in store.list():
        print(f"{a['kind']:9} {a['id']:20} v{a['version']} {a['status']:11} score={a['score']}")
    return 0


def cmd_artifact_add(args) -> int:
    store = ArtifactStore(args.root)
    content = args.content
    if not content and args.file:
        content = Path(args.file).read_text(encoding="utf-8")
    if not content:
        content = sys.stdin.read()
    if not content.strip():
        print("no content provided (use --content, --file, or stdin)", file=sys.stderr)
        return 1
    store.create(args.kind, args.name, content)
    print(f"created {args.kind}/{args.name} v1")
    return 0


def cmd_seed_report(args) -> int:
    from evals.generator import main as gen_main
    sys.argv = ["evals.generator", "--out", args.out]
    gen_main()
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

    sr = sub.add_parser("seed-report", help="expand seed eval set to JSON")
    sr.add_argument("--out", default="")
    sr.set_defaults(func=cmd_seed_report)

    args = ap.parse_args()
    sys.exit(args.func(args))


if __name__ == "__main__":
    main()
