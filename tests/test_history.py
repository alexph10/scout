import json
from datetime import datetime, timezone
from pathlib import Path

from src.history import recently_seen


def _write(data_dir: Path, date_str: str, full_names: list[str]) -> None:
    payload = {
        "generated_at": f"{date_str}T00:00:00+00:00",
        "count": len(full_names),
        "repos": [{"full_name": name} for name in full_names],
    }
    (data_dir / f"{date_str}.json").write_text(json.dumps(payload), encoding="utf-8")


NOW = datetime(2026, 5, 31, tzinfo=timezone.utc)


def test_window_zero_returns_empty(tmp_path):
    _write(tmp_path, "2026-05-30", ["a/x"])
    assert recently_seen(tmp_path, 0, NOW) == set()


def test_missing_dir_returns_empty(tmp_path):
    assert recently_seen(tmp_path / "nope", 7, NOW) == set()


def test_reads_files_within_window(tmp_path):
    _write(tmp_path, "2026-05-29", ["a/recent"])
    _write(tmp_path, "2026-05-30", ["b/yesterday"])
    assert recently_seen(tmp_path, 7, NOW) == {"a/recent", "b/yesterday"}


def test_excludes_today(tmp_path):
    _write(tmp_path, "2026-05-31", ["today/repo"])
    _write(tmp_path, "2026-05-30", ["yesterday/repo"])
    assert recently_seen(tmp_path, 7, NOW) == {"yesterday/repo"}


def test_excludes_older_than_window(tmp_path):
    _write(tmp_path, "2026-05-20", ["too/old"])      # 11 days ago
    _write(tmp_path, "2026-05-25", ["just/in"])      # 6 days ago, window=7
    assert recently_seen(tmp_path, 7, NOW) == {"just/in"}


def test_ignores_non_date_filenames(tmp_path):
    (tmp_path / "notes.json").write_text(
        json.dumps({"repos": [{"full_name": "nope/nope"}]}), encoding="utf-8"
    )
    _write(tmp_path, "2026-05-30", ["good/repo"])
    assert recently_seen(tmp_path, 7, NOW) == {"good/repo"}


def test_ignores_malformed_json(tmp_path):
    _write(tmp_path, "2026-05-29", ["ok/repo"])
    (tmp_path / "2026-05-30.json").write_text("not json {", encoding="utf-8")
    assert recently_seen(tmp_path, 7, NOW) == {"ok/repo"}


def test_unions_across_multiple_days(tmp_path):
    _write(tmp_path, "2026-05-28", ["a/1", "b/2"])
    _write(tmp_path, "2026-05-29", ["b/2", "c/3"])
    _write(tmp_path, "2026-05-30", ["d/4"])
    assert recently_seen(tmp_path, 7, NOW) == {"a/1", "b/2", "c/3", "d/4"}
