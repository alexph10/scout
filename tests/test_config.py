import os

from src.config import load_dotenv


def test_load_dotenv_parses_basic_pairs(tmp_path, monkeypatch):
    env = tmp_path / ".env"
    env.write_text(
        "# a comment\n"
        "\n"
        "GITHUB_TOKEN=ghp_abc123\n"
        'QUOTED="value with spaces"\n'
        "SINGLE='single quoted'\n"
        "export EXPORTED=exported_val\n",
        encoding="utf-8",
    )

    for key in ["GITHUB_TOKEN", "QUOTED", "SINGLE", "EXPORTED"]:
        monkeypatch.delenv(key, raising=False)

    loaded = load_dotenv(env)
    assert loaded["GITHUB_TOKEN"] == "ghp_abc123"
    assert loaded["QUOTED"] == "value with spaces"
    assert loaded["SINGLE"] == "single quoted"
    assert loaded["EXPORTED"] == "exported_val"
    assert os.environ["GITHUB_TOKEN"] == "ghp_abc123"


def test_load_dotenv_does_not_override_existing(tmp_path, monkeypatch):
    env = tmp_path / ".env"
    env.write_text("GITHUB_TOKEN=from_file\n", encoding="utf-8")
    monkeypatch.setenv("GITHUB_TOKEN", "from_shell")

    load_dotenv(env)
    assert os.environ["GITHUB_TOKEN"] == "from_shell"


def test_load_dotenv_override_flag(tmp_path, monkeypatch):
    env = tmp_path / ".env"
    env.write_text("GITHUB_TOKEN=from_file\n", encoding="utf-8")
    monkeypatch.setenv("GITHUB_TOKEN", "from_shell")

    load_dotenv(env, override=True)
    assert os.environ["GITHUB_TOKEN"] == "from_file"


def test_load_dotenv_missing_file_is_noop(tmp_path):
    assert load_dotenv(tmp_path / "does-not-exist.env") == {}
