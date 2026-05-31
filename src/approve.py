"""Interactive starring of shortlisted repos."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .config import DATA_DIR
from .github_client import GitHubClient


def _load_shortlist(arg: str) -> list[dict]:
    path = Path(arg)
    if path.suffix == ".json" and path.exists():
        return json.loads(path.read_text(encoding="utf-8"))["repos"]
    if path.suffix == ".md" and path.exists():
        json_path = DATA_DIR / (path.stem + ".json")
        return json.loads(json_path.read_text(encoding="utf-8"))["repos"]
    json_path = DATA_DIR / f"{arg}.json"
    if json_path.exists():
        return json.loads(json_path.read_text(encoding="utf-8"))["repos"]
    raise FileNotFoundError(f"Could not resolve shortlist for: {arg}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Walk through today's shortlist and star the ones you like."
    )
    parser.add_argument(
        "shortlist",
        help="A reports/*.md, a data/*.json, or just a YYYY-MM-DD.",
    )
    parser.add_argument(
        "--yes-to-all",
        action="store_true",
        help="Star everything without asking.",
    )
    args = parser.parse_args(argv)

    repos = _load_shortlist(args.shortlist)
    if not repos:
        print("Shortlist is empty.")
        return 0

    client = GitHubClient()
    if not client.token:
        print("GITHUB_TOKEN is required to star repos.", file=sys.stderr)
        return 2

    starred = 0
    skipped = 0
    for repo in repos:
        full_name = repo["full_name"]
        if client.is_starred(full_name):
            print(f"already starred: {full_name}")
            continue

        if args.yes_to_all:
            answer = "y"
        else:
            answer = input(f"Star {full_name}? [y/N/q] ").strip().lower()
            if answer == "q":
                break

        if answer == "y":
            client.star(full_name)
            print(f"starred: {full_name}")
            starred += 1
        else:
            print(f"skipped: {full_name}")
            skipped += 1

    print(f"\nDone. starred={starred} skipped={skipped} total={len(repos)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
