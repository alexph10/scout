import json
from unittest.mock import patch

from src import cli


def test_help_flag_prints_help_and_exits_zero(capsys):
    rc = cli.main(["--help"])
    out = capsys.readouterr().out
    assert rc == 0
    assert "scout" in out
    assert "run" in out and "approve" in out and "show" in out and "list" in out


def test_version_flag(capsys):
    rc = cli.main(["--version"])
    out = capsys.readouterr().out
    assert rc == 0
    assert out.strip().startswith("scout ")


def test_unknown_command_returns_2_and_prints_help(capsys):
    rc = cli.main(["bogus"])
    captured = capsys.readouterr()
    assert rc == 2
    assert "unknown command" in captured.err


def test_no_args_dispatches_to_run():
    with patch("src.cli.cmd_run", return_value=0) as mock:
        rc = cli.main([])
    assert rc == 0
    mock.assert_called_once_with([])


def test_run_subcommand_forwards_args():
    with patch("src.cli.cmd_run", return_value=0) as mock:
        cli.main(["run", "--date", "2026-05-31"])
    mock.assert_called_once_with(["--date", "2026-05-31"])


def test_top_level_flag_treated_as_implicit_run():
    with patch("src.cli.cmd_run", return_value=0) as mock:
        cli.main(["--date", "2026-05-31"])
    mock.assert_called_once_with(["--date", "2026-05-31"])


def test_approve_subcommand_forwards_args():
    with patch("src.cli.approve_main", return_value=0) as mock:
        cli.main(["approve", "2026-05-31", "--yes-to-all"])
    mock.assert_called_once_with(["2026-05-31", "--yes-to-all"])


def test_show_prints_latest_report(tmp_path, monkeypatch, capsys):
    reports = tmp_path / "reports"
    reports.mkdir()
    (reports / "2026-05-30.md").write_text("# old\n", encoding="utf-8")
    (reports / "2026-05-31.md").write_text("# newest\n", encoding="utf-8")
    monkeypatch.setattr(cli, "REPORTS_DIR", reports)

    rc = cli.main(["show"])
    out = capsys.readouterr().out
    assert rc == 0
    assert "newest" in out


def test_show_specific_date(tmp_path, monkeypatch, capsys):
    reports = tmp_path / "reports"
    reports.mkdir()
    (reports / "2026-05-30.md").write_text("# may-30\n", encoding="utf-8")
    (reports / "2026-05-31.md").write_text("# may-31\n", encoding="utf-8")
    monkeypatch.setattr(cli, "REPORTS_DIR", reports)

    rc = cli.main(["show", "2026-05-30"])
    out = capsys.readouterr().out
    assert rc == 0
    assert "may-30" in out
    assert "may-31" not in out


def test_show_missing_report_errors(tmp_path, monkeypatch, capsys):
    reports = tmp_path / "reports"
    reports.mkdir()
    monkeypatch.setattr(cli, "REPORTS_DIR", reports)

    rc = cli.main(["show"])
    assert rc == 1
    assert "no report found" in capsys.readouterr().err.lower()


def test_list_shows_reports_with_counts(tmp_path, monkeypatch, capsys):
    data = tmp_path / "data"
    data.mkdir()
    (data / "2026-05-30.json").write_text(json.dumps({"count": 5, "repos": []}), encoding="utf-8")
    (data / "2026-05-31.json").write_text(json.dumps({"count": 3, "repos": []}), encoding="utf-8")
    monkeypatch.setattr(cli, "DATA_DIR", data)

    rc = cli.main(["list"])
    out = capsys.readouterr().out
    assert rc == 0
    assert "2026-05-30" in out and "5" in out
    assert "2026-05-31" in out and "3" in out


def test_list_empty(tmp_path, monkeypatch, capsys):
    data = tmp_path / "data"
    data.mkdir()
    monkeypatch.setattr(cli, "DATA_DIR", data)

    rc = cli.main(["list"])
    out = capsys.readouterr().out
    assert rc == 0
    assert "no reports" in out.lower()
