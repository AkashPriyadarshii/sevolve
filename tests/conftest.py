"""Shared fixtures — hermetic, no network, no API key.

The executor is mocked to return canned output per task; the judge/optimizer
are scripted clients returning JSON. The full loop is testable offline.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from engine.artifact import ArtifactStore  # noqa: E402
from engine.grader import make_contains, make_length  # noqa: E402


@pytest.fixture()
def store(tmp_path):
    return ArtifactStore(tmp_path / "artifacts")


@pytest.fixture()
def seed_eval_set():
    return {
        "artifact": {"kind": "skill", "id": "concise-summary"},
        "tasks": [
            {
                "id": "sum-1",
                "task": "Summarize in at most 40 words keeping main point + date:\n"
                        "The RBI announced on 2026-07-15 repo rates cut by 25bps.",
                "_graders": {
                    "contains_date": make_contains("2026-07-15"),
                    "max_40_words": make_length(1, 280),
                },
            },
            {
                "id": "sum-2",
                "task": "Summarize in at most 40 words keeping main point + number:\n"
                        "64% of enterprises run most workloads in cloud.",
                "_graders": {
                    "contains_64": make_contains("64"),
                    "max_40_words": make_length(1, 280),
                },
            },
        ],
    }


@pytest.fixture()
def make_executor():
    """Return an executor factory keyed on task text -> output."""

    def _make(outputs: dict[str, str]):
        def run_exec(artifact, task, trace=None, timeout=300):
            if trace is not None:
                trace.tool("executor", args="claude -p")
                trace.ok = True
            for key, out in outputs.items():
                if key in task:
                    if trace is not None:
                        trace.add("output", text=out)
                    return out
            return ""
        return run_exec

    return _make


@pytest.fixture()
def scripted_client():
    """Judge + optimizer as a scripted client. complete() inspects the prompt
    to decide judge vs optimizer and returns deterministic JSON."""
    call_log = []

    def complete(prompt: str) -> str:
        call_log.append(prompt)
        if "GRADER SCORES" in prompt:  # optimizer plan prompt
            return json.dumps({
                "critique": "skill lacked a length cap; proposed explicit caps.",
                "variants": [
                    {"content": "1. Keep the main point. 2. Keep exact dates/numbers. "
                                "3. Hard cap: max 40 words. 4. No padding.",
                     "rationale": "adds explicit caps"},
                    {"content": "brief but complete",
                     "rationale": "shorter"},
                ],
            })
        return json.dumps({"score": 0.9, "reasoning": "good, concise", "rubric_ok": True})

    complete.calls = call_log
    return complete


@pytest.fixture()
def ctx(scripted_client):
    return {"client": scripted_client, "ci": True, "max_size": 16_000}
