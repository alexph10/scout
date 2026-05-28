"""Stage 1: collect candidate repos from search queries + curated lists."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

from .github_client import GitHubClient


def _query_placeholders(now: datetime) -> dict[str, str]:
    return {
        "today": now.date().isoformat(),
        "seven_days_ago": (now - timedelta(days=7)).date().isoformat(),
        "thirty_days_ago": (now - timedelta(days=30)).date().isoformat(),
        "ninety_days_ago": (now - timedelta(days=90)).date().isoformat(),
    }


def collect(
    sources: dict[str, Any],
    client: GitHubClient,
    now: datetime | None = None,
) -> list[dict[str, Any]]:
    """Return a deduplicated list of raw repo dicts from all configured sources."""
    now = now or datetime.now(timezone.utc)
    placeholders = _query_placeholders(now)
    defaults = sources.get("defaults") or {}
    per_page = int(defaults.get("per_page", 30))
    max_per_query = int(defaults.get("max_per_query", per_page))

    seen: dict[str, dict[str, Any]] = {}

    for query in sources.get("queries") or []:
        q = query["q"].format(**placeholders)
        items = client.search_repositories(
            q=q,
            sort=query.get("sort", "stars"),
            order=query.get("order", "desc"),
            per_page=per_page,
        )
        for repo in items[:max_per_query]:
            repo["_source"] = query.get("name", "search")
            seen.setdefault(repo["full_name"], repo)

    for full_name in sources.get("curated") or []:
        if full_name in seen:
            continue
        repo = client.get_repository(full_name)
        repo["_source"] = "curated"
        seen[full_name] = repo

    return list(seen.values())
