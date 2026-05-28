"""Orchestrates collect → score → publish for the daily shortlist."""

from __future__ import annotations

import argparse
import sys
from datetime import datetime, timezone

from .collect import collect
from .config import load_scoring, load_sources
from .github_client import GitHubClient
from .publish import publish
from .score import rank


def run(now: datetime | None = None) -> int:
    now = now or datetime.now(timezone.utc)
    sources = load_sources()
    scoring = load_scoring()

    client = GitHubClient()
    candidates = collect(sources, client, now=now)
    if not candidates:
        print("No candidates collected.", file=sys.stderr)

    ranked = rank(candidates, scoring, now=now)
    shortlist_size = int(scoring.get("shortlist_size", 5))
    shortlist = ranked[:shortlist_size]

    json_path, md_path = publish(shortlist, date=now)
    print(f"Wrote {len(shortlist)} repos.")
    print(f"  data:   {json_path}")
    print(f"  report: {md_path}")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run the daily shortlist pipeline.")
    parser.add_argument(
        "--date",
        help="Override the run date (YYYY-MM-DD, UTC). Defaults to today.",
    )
    args = parser.parse_args(argv)

    now = None
    if args.date:
        now = datetime.fromisoformat(args.date).replace(tzinfo=timezone.utc)
    return run(now=now)


if __name__ == "__main__":
    raise SystemExit(main())
