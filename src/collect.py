"""Pull candidate repos from search queries and curated list."""

from __future__ import annotations

import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta, timezone
from typing import Any

from .github_client import GitHubClient


MAX_WORKERS = 6  # GitHub authed search allows 30 req/min; well under cap.


def _query_placeholders(now: datetime) -> dict[str, str]:
    return {
        "today": now.date().isoformat(),
        "seven_days_ago": (now - timedelta(days=7)).date().isoformat(),
        "thirty_days_ago": (now - timedelta(days=30)).date().isoformat(),
        "ninety_days_ago": (now - timedelta(days=90)).date().isoformat(),
    }


def passes_filters(repo: dict[str, Any], filters: dict[str, Any]) -> bool:
    """Drop repos that fail quality filters: archived, forks, short descriptions."""
    if filters.get("exclude_archived", True) and repo.get("archived"):
        return False
    if filters.get("exclude_forks", True) and repo.get("fork"):
        return False
    min_desc = int(filters.get("min_description_length", 0))
    if min_desc > 0:
        desc = (repo.get("description") or "").strip()
        if len(desc) < min_desc:
            return False
    return True


def collect(
    sources: dict[str, Any],
    client: GitHubClient,
    now: datetime | None = None,
) -> list[dict[str, Any]]:
    now = now or datetime.now(timezone.utc)
    placeholders = _query_placeholders(now)
    defaults = sources.get("defaults") or {}
    per_page = int(defaults.get("per_page", 30))
    max_per_query = int(defaults.get("max_per_query", per_page))
    filters = defaults.get("filters") or {}
    queries = sources.get("queries") or []

    # Fan out search queries in parallel - this is the main runtime cost.
    results: list[tuple[int, str, list[dict[str, Any]] | Exception]] = []

    def _run(idx: int, query: dict[str, Any]) -> tuple[int, str, Any]:
        name = query.get("name", f"query-{idx}")
        try:
            items = client.search_repositories(
                q=query["q"].format(**placeholders),
                sort=query.get("sort", "stars"),
                order=query.get("order", "desc"),
                per_page=per_page,
            )
            return idx, name, items
        except Exception as exc:  # noqa: BLE001 - reported per-query
            return idx, name, exc

    print(f"Searching {len(queries)} queries in parallel...", file=sys.stderr)
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as pool:
        futures = [pool.submit(_run, i, q) for i, q in enumerate(queries)]
        for fut in as_completed(futures):
            idx, name, payload = fut.result()
            if isinstance(payload, Exception):
                print(f"  {name}: FAILED ({payload})", file=sys.stderr)
            else:
                print(f"  {name}: {len(payload)} hits", file=sys.stderr)
            results.append((idx, name, payload))

    # Replay in original query order so dedup is deterministic.
    results.sort(key=lambda t: t[0])
    seen: dict[str, dict[str, Any]] = {}
    for idx, name, payload in results:
        if isinstance(payload, Exception):
            continue
        for repo in payload[:max_per_query]:
            if not passes_filters(repo, filters):
                continue
            repo["_source"] = name
            seen.setdefault(repo["full_name"], repo)

    # Curated entries bypass filters - they are explicit user picks.
    curated = [n for n in (sources.get("curated") or []) if n not in seen]
    if curated:
        print(f"Fetching {len(curated)} curated repo(s)...", file=sys.stderr)
        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as pool:
            for repo in pool.map(client.get_repository, curated):
                repo["_source"] = "curated"
                seen[repo["full_name"]] = repo

    return list(seen.values())
