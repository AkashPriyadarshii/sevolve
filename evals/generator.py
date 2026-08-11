"""Generate eval sets from seed templates — bring-your-own-tasks path.

Run: python -m evals.generator  (prints an expanded eval set to stdout)
Pass --out FILE to write JSON. The seed file ships real task-shaped examples;
this generator makes it trivial to extend to your own domain.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from engine.grader import make_contains, make_length


def expand_seed(seed_path: Path) -> dict:
    data = json.loads(seed_path.read_text(encoding="utf-8"))
    for task in data["tasks"]:
        graders = {}
        for spec in task["graders"]:
            if spec["type"] == "contains":
                graders[spec["name"]] = make_contains(spec["value"])
            elif spec["type"] == "length":
                graders[spec["name"]] = make_length(spec["lo"], spec["hi"])
            elif spec["type"] == "exact":
                from engine.grader import make_exact
                graders[spec["name"]] = make_exact(spec["value"])
            else:
                raise ValueError(f"unknown grader type {spec['type']!r} in {spec['name']}")
        task["_graders"] = graders
    return data


def main() -> None:
    ap = argparse.ArgumentParser(description="expand seed eval set into a JSON report")
    ap.add_argument("--seed", default=str(Path(__file__).parent / "seed.json"))
    ap.add_argument("--out", default="")
    args = ap.parse_args()
    data = expand_seed(Path(args.seed))
    # Don't serialize the live grader objects; report the expansion shape.
    for task in data["tasks"]:
        task["_graders"] = {k: v.__name__ for k, v in task["_graders"].items()}
    text = json.dumps(data, indent=2)
    if args.out:
        Path(args.out).write_text(text, encoding="utf-8")
    else:
        sys.stdout.write(text + "\n")


if __name__ == "__main__":
    main()
