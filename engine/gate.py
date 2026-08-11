"""Promotion gates — a variant promotes only if ALL gates pass.

The evaluator sits OUTSIDE the evolution loop (Lilian Weng). `--ci` overrides
human approval, never the mechanical gates. Every gate returns (ok: bool,
detail: str). Mechanical gates run in the same read-only spirit as graders:
size limits, semantic-preservation on a regression set, and (optionally) the
candidate's own tests.
"""

from __future__ import annotations

from typing import Any, Callable

from .grader import weighted_score
from .trace import Trace

Gate = Callable[[dict[str, Any]], tuple[bool, str]]


def size_limit(max_bytes: int) -> Gate:
    def g(ctx: dict[str, Any]) -> tuple[bool, str]:
        size = len(ctx["artifact"]["content"].encode("utf-8"))
        ok = size <= max_bytes
        return ok, f"size={size}B limit={max_bytes}B {'ok' if ok else 'TOO BIG'}"
    return g


def regression_holds(prev_score: float, min_delta: float = -0.05) -> Gate:
    """New artifact must not score meaningfully below the previous best on the
    held-out/regression set."""
    def g(ctx: dict[str, Any]) -> tuple[bool, str]:
        new_score = ctx.get("new_score")
        if new_score is None:
            return False, "no new_score in gate ctx"
        ok = new_score >= prev_score + min_delta
        return ok, f"regression: prev={prev_score:.3f} new={new_score:.3f} {'ok' if ok else 'REGRESSED'}"
    return g


def human_approval(prompt_fn: Callable[[dict[str, Any]], bool] | None = None) -> Gate:
    """Default: prompt for approval. With --ci, prompt_fn returns True without
    asking. Never skips the mechanical gates."""
    def g(ctx: dict[str, Any]) -> tuple[bool, str]:
        if prompt_fn is not None and prompt_fn(ctx):
            return True, "approved (--ci)"
        # interactive fallback
        print("\n--- proposed artifact ---")
        print(ctx["artifact"]["content"])
        answer = input("Approve promotion? [y/N] ").strip().lower()
        ok = answer in {"y", "yes"}
        return ok, "human approved" if ok else "human rejected"
    return g


def run_gates(gates: list[Gate], ctx: dict[str, Any]) -> tuple[bool, list[tuple[str, str]]]:
    results = []
    for g in gates:
        name = getattr(g, "__name__", g.__class__.__name__)
        ok, detail = g(ctx)
        results.append((name, detail))
        if not ok:
            return False, results
    return True, results
