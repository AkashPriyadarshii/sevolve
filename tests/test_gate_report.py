from pathlib import Path

from engine.gate import human_approval, regression_holds, run_gates, size_limit
from engine.report import render, write


def test_size_limit_gate():
    g = size_limit(50)
    ok, detail = g({"artifact": {"content": "short content"}})
    assert ok is True
    assert "ok" in detail

    ok_fail, detail_fail = g({"artifact": {"content": "x" * 100}})
    assert ok_fail is False
    assert "TOO BIG" in detail_fail


def test_regression_holds_gate():
    g = regression_holds(prev_score=0.80, min_delta=-0.05)
    ok, _ = g({"new_score": 0.82})
    assert ok is True

    ok_within_margin, _ = g({"new_score": 0.76})
    assert ok_within_margin is True

    ok_drop, _ = g({"new_score": 0.60})
    assert ok_drop is False


def test_human_approval_ci():
    g = human_approval(prompt_fn=lambda ctx: True)
    ok, detail = g({"ci": True, "artifact": {"content": "foo"}})
    assert ok is True
    assert "approved (--ci)" in detail


def test_run_gates_combined():
    gates = [
        size_limit(100),
        regression_holds(0.5),
    ]
    ok, results = run_gates(gates, {"artifact": {"content": "hello"}, "new_score": 0.9})
    assert ok is True
    assert len(results) == 2


def test_report_render_and_write(tmp_path):
    run_data = {
        "artifact": {"kind": "skill", "id": "test-skill"},
        "promoted": True,
        "best_score": 0.92,
        "history": [{"iter": 1, "train_score": 0.5, "best_held": 0.92, "improved": True, "judge_reasoning": "great"}],
        "gate_results": [("size_limit", "size=50B limit=16000B ok")],
    }
    rendered = render(run_data, prev_score=0.60)
    assert "artifact: `skill/test-skill`" in rendered
    assert "promoted: **True**" in rendered
    assert "**best score: 0.920**" in rendered
    assert "delta: **+0.320**" in rendered

    out_path = write(run_data, prev_score=0.60, report_dir=tmp_path / "reports")
    assert out_path.exists()
    assert out_path.read_text(encoding="utf-8") == rendered
