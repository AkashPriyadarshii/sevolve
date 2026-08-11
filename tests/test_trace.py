"""Trace: capture, save/load, render."""

from engine.trace import Trace, save, load_all, trace_to_text


def test_capture_save_load(tmp_path):
    t = Trace(task="summarize x")
    t.tool("executor", args="claude -p", result="done")
    t.failure("timeout", "exceeded 300s")
    t.ok = False
    save(t, tmp_path)

    loaded = load_all(tmp_path)
    assert len(loaded) == 1
    tid, back = loaded[0]
    assert back.task == "summarize x"
    assert back.events[0]["kind"] == "tool_call"
    assert back.events[1]["kind"] == "failure"
    assert back.ok is False


def test_render_includes_failure():
    t = Trace(task="t")
    t.failure("oops", "detail")
    text = trace_to_text(t)
    assert "FAILED reason='oops'" in text
    assert "TASK: t" in text


def test_trace_dict_roundtrip():
    t = Trace(task="t")
    t.add("custom", k=1)
    back = Trace.from_dict(t.to_dict())
    assert back.to_dict() == t.to_dict()
