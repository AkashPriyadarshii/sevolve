from pathlib import Path

from engine.artifact import ArtifactStore
from engine.promote import parse_report, promote_artifact


def test_parse_report_markdown(tmp_path):
    report_file = tmp_path / "report-test.md"
    report_file.write_text(
        "# sevolve run report\n\n"
        "artifact: `skill/concise-summary`  promoted: **True**\n\n"
        "**best score: 0.950**\n\n"
        "## Gates\n- size_limit: ok\n",
        encoding="utf-8",
    )
    parsed = parse_report(report_file)
    assert parsed is not None
    assert parsed["kind"] == "skill"
    assert parsed["id"] == "concise-summary"
    assert parsed["promoted"] is True
    assert parsed["best_score"] == 0.95


def test_parse_report_not_promoted(tmp_path):
    report_file = tmp_path / "report-test.md"
    report_file.write_text(
        "# sevolve run report\n\n"
        "artifact: `prompt/coder`  promoted: **False**\n\n"
        "**best score: 0.400**\n",
        encoding="utf-8",
    )
    parsed = parse_report(report_file)
    assert parsed is not None
    assert parsed["promoted"] is False


def test_promote_artifact_mocked_git(tmp_path):
    store = ArtifactStore(tmp_path / "artifacts")
    store.create("skill", "concise-summary", "good skill content")

    report_file = tmp_path / "report.md"
    report_file.write_text(
        "# sevolve run report\n\n"
        "artifact: `skill/concise-summary`  promoted: **True**\n\n"
        "**best score: 0.950**\n",
        encoding="utf-8",
    )

    commands_run = []

    def mock_runner(cmd, cwd=None):
        commands_run.append(" ".join(cmd))
        if cmd[0] == "gh":
            return 0, "https://github.com/AkashPriyadarshii/sevolve/pull/1", ""
        return 0, "", ""

    ok, pr_url = promote_artifact(
        "skill/concise-summary",
        report_file,
        artifacts_dir=tmp_path / "artifacts",
        runner=mock_runner,
    )

    assert ok is True
    assert "pull/1" in pr_url
    assert any("git checkout -b promote/skill/concise-summary" in c for c in commands_run)
    assert any("gh pr create" in c for c in commands_run)
