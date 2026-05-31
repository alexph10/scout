from datetime import datetime, timedelta, timezone

from src.score import rank, score_repo


SCORING = {
    "weights": {"activity": 0.4, "popularity": 0.3, "language": 0.2, "topic": 0.1},
    "activity_horizon_days": 30,
    "popularity_log_cap": 5,
    "preferred_languages": {"Python": 1.0, "Rust": 0.5},
    "preferred_topics": {"ai": 1.0, "cli": 0.5},
}

NOW = datetime(2026, 5, 28, tzinfo=timezone.utc)


def _repo(**overrides):
    base = {
        "full_name": "owner/example",
        "html_url": "https://github.com/owner/example",
        "description": "test",
        "language": "Python",
        "topics": ["ai"],
        "stargazers_count": 1000,
        "pushed_at": (NOW - timedelta(days=1)).isoformat(),
    }
    base.update(overrides)
    return base


def test_score_fresh_python_ai_repo_scores_high():
    breakdown = score_repo(_repo(), SCORING, now=NOW)
    assert breakdown["activity"] > 0.9
    assert breakdown["language"] == 1.0
    assert breakdown["topic"] == 1.0
    assert 0.0 < breakdown["total"] <= 1.0


def test_old_repo_has_zero_activity():
    breakdown = score_repo(
        _repo(pushed_at=(NOW - timedelta(days=120)).isoformat()),
        SCORING,
        now=NOW,
    )
    assert breakdown["activity"] == 0.0


def test_rank_sorts_descending_by_total():
    repos = [
        _repo(full_name="owner/old", pushed_at=(NOW - timedelta(days=29)).isoformat()),
        _repo(full_name="owner/fresh", pushed_at=NOW.isoformat()),
    ]
    ranked = rank(repos, SCORING, now=NOW)
    assert ranked[0]["full_name"] == "owner/fresh"
    assert ranked[0]["_score"]["total"] >= ranked[1]["_score"]["total"]


def test_unknown_language_and_topic_score_zero():
    breakdown = score_repo(
        _repo(language="COBOL", topics=["mainframe"]),
        SCORING,
        now=NOW,
    )
    assert breakdown["language"] == 0.0
    assert breakdown["topic"] == 0.0
