"""Agent-as-client: completes judge/optimizer prompts via `claude -p`."""

from unittest.mock import patch

from engine.client import ClaudeClient
from engine.executor import ExecutorError


def test_complete_returns_stdout():
    with patch("engine.executor.shutil.which", return_value="/usr/bin/claude"), \
         patch("engine.executor.subprocess.run") as mock_run:
        proc = mock_run.return_value
        proc.returncode = 0
        proc.stdout = '{"score": 0.9, "reasoning": "solid"}'
        out = ClaudeClient().complete("grade this")
        mock_run.assert_called_once()
        assert out == '{"score": 0.9, "reasoning": "solid"}'


def test_complete_raises_on_nonzero():
    with patch("engine.executor.shutil.which", return_value="/usr/bin/claude"), \
         patch("engine.executor.subprocess.run") as mock_run:
        proc = mock_run.return_value
        proc.returncode = 1
        proc.stderr = "boom"
        try:
            ClaudeClient().complete("x")
            assert False, "expected ExecutorError"
        except ExecutorError:
            pass


def test_complete_raises_when_cli_missing():
    with patch("engine.executor.shutil.which", return_value=None):
        try:
            ClaudeClient().complete("x")
            assert False, "expected ExecutorError"
        except ExecutorError:
            pass
