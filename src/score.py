"""Stage 2: score repos with a transparent weighted rubric."""

from __future__ import annotations

import math
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from typing import Any

from dateutil import parser as dateparser


@dataclass
class ScoreBreakdown:
    activity: float
    popularity: float
    language: float
    topic: float
    total: float

    def as_dict(self) -> dict[str, float]:
        return asdict(self)


def _activity_score(pushed_at: str | None, horizon_days: int, now: datetime) -> float:
    if not pushed_at:
        return 0.0
    pushed = dateparser.isoparse(pushed_at)
    if pushed.tzinfo is None:
        pushed = pushed.replace(tzinfo=timezone.utc)
    age_days = max(0.0, (now - pushed).total_seconds() / 86400.0)
    if age_days >= horizon_days:
        return 0.0
    return 1.0 - (age_days / horizon_days)


def _popularity_score(stars: int, log_cap: float) -> float:
    if stars <= 0 or log_cap <= 0:
        return 0.0
    value = math.log10(stars + 1) / log_cap
    return max(0.0, min(1.0, value))


def _language_score(language: str | None, preferred: dict[str, float]) -> float:
    if not language:
        return 0.0
    return float(preferred.get(language, 0.0))


def _topic_score(topics: list[str] | None, preferred: dict[str, float]) -> float:
    if not topics:
        return 0.0
    best = 0.0
    for topic in topics:
        best = max(best, float(preferred.get(topic, 0.0)))
    return best


def score_repo(
    repo: dict[str, Any],
    scoring: dict[str, Any],
    now: datetime | None = None,
) -> ScoreBreakdown:
    now = now or datetime.now(timezone.utc)
    weights = scoring.get("weights", {})

    activity = _activity_score(
        repo.get("pushed_at"),
        int(scoring.get("activity_horizon_days", 30)),
        now,
    )
    popularity = _popularity_score(
        int(repo.get("stargazers_count", 0)),
        float(scoring.get("popularity_log_cap", 5)),
    )
    language = _language_score(
        repo.get("language"),
        scoring.get("preferred_languages", {}),
    )
    topic = _topic_score(
        repo.get("topics"),
        scoring.get("preferred_topics", {}),
    )

    total = (
        weights.get("activity", 0) * activity
        + weights.get("popularity", 0) * popularity
        + weights.get("language", 0) * language
        + weights.get("topic", 0) * topic
    )
    return ScoreBreakdown(activity, popularity, language, topic, round(total, 4))


def rank(
    repos: list[dict[str, Any]],
    scoring: dict[str, Any],
    now: datetime | None = None,
) -> list[dict[str, Any]]:
    """Return repos sorted by score desc, with `_score` attached."""
    out = []
    for repo in repos:
        breakdown = score_repo(repo, scoring, now)
        enriched = dict(repo)
        enriched["_score"] = breakdown.as_dict()
        out.append(enriched)
    out.sort(key=lambda r: r["_score"]["total"], reverse=True)
    return out
