"""Weighted scoring for repos."""

from __future__ import annotations

import math
from datetime import datetime, timezone
from typing import Any


def _parse_ts(ts: str) -> datetime:
    dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
    return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)


def _activity(pushed_at: str | None, horizon_days: int, now: datetime) -> float:
    if not pushed_at:
        return 0.0
    age_days = max(0.0, (now - _parse_ts(pushed_at)).total_seconds() / 86400.0)
    if age_days >= horizon_days:
        return 0.0
    return 1.0 - (age_days / horizon_days)


def _popularity(stars: int, log_cap: float) -> float:
    if stars <= 0 or log_cap <= 0:
        return 0.0
    return max(0.0, min(1.0, math.log10(stars + 1) / log_cap))


def _best_match(values: list[str] | None, preferred: dict[str, float]) -> float:
    if not values:
        return 0.0
    return max((float(preferred.get(v, 0.0)) for v in values), default=0.0)


def score_repo(
    repo: dict[str, Any],
    scoring: dict[str, Any],
    now: datetime | None = None,
) -> dict[str, float]:
    now = now or datetime.now(timezone.utc)
    weights = scoring.get("weights", {})

    activity = _activity(
        repo.get("pushed_at"),
        int(scoring.get("activity_horizon_days", 30)),
        now,
    )
    popularity = _popularity(
        int(repo.get("stargazers_count", 0)),
        float(scoring.get("popularity_log_cap", 5)),
    )
    language = float(scoring.get("preferred_languages", {}).get(repo.get("language") or "", 0.0))
    topic = _best_match(repo.get("topics"), scoring.get("preferred_topics", {}))

    total = (
        weights.get("activity", 0) * activity
        + weights.get("popularity", 0) * popularity
        + weights.get("language", 0) * language
        + weights.get("topic", 0) * topic
    )
    return {
        "activity": activity,
        "popularity": popularity,
        "language": language,
        "topic": topic,
        "total": round(total, 4),
    }


def rank(
    repos: list[dict[str, Any]],
    scoring: dict[str, Any],
    now: datetime | None = None,
) -> list[dict[str, Any]]:
    out = []
    for repo in repos:
        enriched = dict(repo)
        enriched["_score"] = score_repo(repo, scoring, now)
        out.append(enriched)
    out.sort(key=lambda r: r["_score"]["total"], reverse=True)
    return out
