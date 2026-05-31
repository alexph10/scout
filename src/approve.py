"""Interactive starring of shortlisted repos."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .config import DATA_DIR
from .github_client import GitHubClient


def _latest_data() -> Path | None:
    if not DATA_DIR.exists():
        return None
    candidates = sorted(DATA_DIR.glob("*.json"))
    return candidates[-1] if candidates else None


def _resolve_shortlist(arg: str | None) -> Path:
    """Resolve a shortlist argument to a data/*.json path.

    Accepts: a path, a YYYY-MM-DD date, '.', 'latest', or no argument
    (the last two resolve to the most recent saved report).
    """
    if arg in (None, ".", "latest"):
        latest = _latest_data()
        if latest is None:
            raise FileNotFoundError(
                f"No saved shortlists found in {DATA_DIR}. Run `scout` first."
            )
        return latest

    path = Path(arg)
    if path.suffix == ".json" and path.exists():
        return path
    if path.suffix == ".md" and path.exists():
        json_path = DATA_DIR / (path.stem + ".json")
        if json_path.exists():
            return json_path
    json_path = DATA_DIR / f"{arg}.json"
    if json_path.exists():
        return json_path
    raise FileNotFoundError(f"Could not resolve shortlist for: {arg}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="scout approve",
        description="Walk a shortlist and star the repos you like. "
                    "Use '.' or omit the argument to act on the latest report.",
    )
    parser.add_argument(
        "shortlist",
        nargs="?",
        default=".",
        help="A reports/*.md path, a data/*.json path, a YYYY-MM-DD, or '.' for latest.",
    )
    parser.add_argument(
        "--yes-to-all",
        action="store_true",
        help="Star everything without asking.",
    )
    args = parser.parse_args(argv)

    try:
        data_path = _resolve_shortlist(args.shortlist)
    except FileNotFoundError as exc:
        print(f"scout: {exc}", file=sys.stderr)
        return 1

    repos = json.loads(data_path.read_text(encoding="utf-8"))["repos"]
    if not repos:
        print("Shortlist is empty.")
        return 0

    client = GitHubClient()
    if not client.token:
        print(
            "scout: no GitHub token found. Set GITHUB_TOKEN, put it in "
            "~/.scout/.env, or run `gh auth login`.",
            file=sys.stderr,
        )
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
