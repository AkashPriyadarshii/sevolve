"""Graders + judge: known-good beats known-bad (P2 verification)."""

import json

from engine.grader import evaluate, weighted_score, make_contains, make_length, make_exact
from engine.judge import build_prompt, judge_score, run_judge
from engine.trace import Trace


def test_known_good_beats_known_bad():
    task = "keep the date"
    graders = {"contains_date": make_contains("2026-07-15"), "length": make_length(1, 280)}
    good = Trace(task=task)
    good.ok = True
    bad = Trace(task=task)
    bad.ok = False

    g = evaluate(graders, task, good, "On 2026-07-15 the RBI cut rates. Short.")
    b = evaluate(graders, task, bad, "something about weather, no date at all")
    assert weighted_score(g) > weighted_score(b)


def test_exact_and_contains():
    assert make_exact("a b c")("t", Trace(task="t"), "a b c") == 1.0
    assert make_exact("a b c")("t", Trace(task="t"), "a b c ") == 1.0  # stripped compare
    assert make_exact("a b c")("t", Trace(task="t"), "a b d") == 0.0
    assert make_contains("needle")("t", Trace(task="t"), "has needle here") == 1.0


def test_judge_parses_json():
    class Fake:
        def complete(self, prompt):
            return json.dumps({"score": 0.9, "reasoning": "solid", "rubric_ok": True})

    prompt = build_prompt("task", Trace(task="task"), "out")
    result = run_judge(prompt, {"client": Fake()})
    assert judge_score(result) == 0.9
    assert result["reasoning"] == "solid"


def test_judge_parses_markdown_json():
    class Fake:
        def complete(self, prompt):
            return "```json\n" + json.dumps({"score": 0.88, "reasoning": "markdown formatted", "rubric_ok": True}) + "\n```"

    prompt = build_prompt("task", Trace(task="task"), "out")
    result = run_judge(prompt, {"client": Fake()})
    assert judge_score(result) == 0.88
    assert result["reasoning"] == "markdown formatted"
    assert result["rubric_ok"] is True


def test_regex_grader():
    from engine.grader import make_regex
    g = make_regex(r"\b202[0-9]-[0-1][0-9]-[0-3][0-9]\b")
    assert g("t", Trace(task="t"), "Date is 2026-07-15") == 1.0
    assert g("t", Trace(task="t"), "No date") == 0.0


def test_judge_handles_non_json():
    class Fake:
        def complete(self, prompt):
            return "not json at all"

    result = run_judge("p", {"client": Fake()})
    assert judge_score(result) == 0.0
    assert result["rubric_ok"] is False
