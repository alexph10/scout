"""Read prior shortlists to support cross-day deduplication."""

from __future__ import annotations

import json
from datetime import date, datetime, timedelta
from pathlib import Path


def recently_seen(
    data_dir: Path,
    window_days: int,
    now: datetime,
) -> set[str]:
    """Return the set of repo full_names that appeared in any shortlist
    written within the last `window_days` days, NOT including today.

    Today is excluded so re-running the pipeline on the same day does not
    dedup against its own previous output.

    Returns an empty set if window_days <= 0 or the data dir is empty.
    """
    seen: set[str] = set()
    if window_days <= 0 or not data_dir.exists():
        return seen

    today = now.date()
    cutoff = today - timedelta(days=window_days)

    for path in data_dir.glob("*.json"):
        try:
            file_date = date.fromisoformat(path.stem)
        except ValueError:
            continue
        if file_date < cutoff or file_date >= today:
            continue
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        for repo in data.get("repos", []) or []:
            name = repo.get("full_name")
            if name:
                seen.add(name)
    return seen
