import json
from pathlib import Path

from engine.ingest import ingest_file, parse_claude_transcript, parse_generic_jsonl
from engine.trace import load_all


def test_parse_generic_jsonl():
    lines = [
        json.dumps({"task": "task 1", "events": [], "output": "out 1", "ok": True}),
        json.dumps({"task": "task 2", "events": [{"kind": "failure", "reason": "timeout"}], "output": "", "ok": False}),
    ]
    text = "\n".join(lines)
    traces = parse_generic_jsonl(text)
    assert len(traces) == 2
    assert traces[0].task == "task 1"
    assert traces[0].ok is True
    assert traces[1].ok is False


def test_parse_claude_transcript():
    transcript = (
        '{"type": "USER_INPUT", "content": "Write a python script"}\n'
        '{"type": "PLANNER_RESPONSE", "content": "Sure, creating it.", "tool_calls": [{"name": "write_to_file", "arguments": {"TargetFile": "test.py"}}]}\n'
        '{"type": "TOOL_RESULT", "content": "Created file test.py", "is_error": false}\n'
    )
    traces = parse_claude_transcript(transcript)
    assert len(traces) == 1
    assert traces[0].task == "Write a python script"
    assert traces[0].ok is True
    assert len(traces[0].events) == 2


def test_ingest_file_end_to_end(tmp_path):
    source = tmp_path / "claude_session.jsonl"
    source.write_text(
        '{"type": "USER_INPUT", "content": "Debug error"}\n'
        '{"type": "PLANNER_RESPONSE", "content": "Fixed.", "status": "DONE"}\n',
        encoding="utf-8",
    )
    traces_dir = tmp_path / "traces"
    tids = ingest_file(source, traces_dir=traces_dir)
    assert len(tids) == 1

    loaded = load_all(traces_dir=traces_dir)
    assert len(loaded) == 1
    assert loaded[0][1].task == "Debug error"
