"""Graders — hard, deterministic checks on task output.

The fidelity of the graders IS the quality lever (OpenAI cookbook lesson):
the optimizer can only improve as much as the graders can see. Graders are
blind — they score output, never see the proposed artifact. Each grader is a
function (task, trace, output) -> 0..1. Run in a separate read-only process
so a hostile/buggy evolution can't reach them.
"""

from __future__ import annotations

from typing import Any, Callable

from .trace import Trace

# Grader fn: (task: str, trace: Trace, output: str) -> float in [0, 1]
Grader = Callable[[str, Trace, str], float]


def lenient_threshold(score: float) -> bool:
    return score >= 0.85


def passes(score: float, threshold: float = 0.85) -> bool:
    return score >= threshold


def exact_match(task: str, trace: Trace, output: str, expected: str) -> float:
    return 1.0 if output.strip() == expected.strip() else 0.0


def contains(task: str, trace: Trace, output: str, needle: str) -> float:
    return 1.0 if needle in output.strip() else 0.0


def length_within(task: str, trace: Trace, output: str, lo: int = 0, hi: int = 1_000_000) -> float:
    n = len(output.strip())
    return 1.0 if lo <= n <= hi else 0.0


# Factories keep seeds declarative.
def make_exact(expected: str) -> Grader:
    return lambda task, trace, output: exact_match(task, trace, output, expected)


def make_contains(needle: str) -> Grader:
    return lambda task, trace, output: contains(task, trace, output, needle)


def make_length(lo: int, hi: int) -> Grader:
    return lambda task, trace, output: length_within(task, trace, output, lo, hi)


def evaluate(graders: dict[str, Grader], task: str, trace: Trace, output: str) -> dict[str, float]:
    return {name: round(g(task, trace, output), 3) for name, g in graders.items()}


def weighted_score(grades: dict[str, float]) -> float:
    return round(sum(grades.values()) / len(grades), 3) if grades else 0.0
