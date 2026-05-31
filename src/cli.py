"""scout - daily GitHub repo shortlist."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

from . import __version__
from .approve import main as approve_main
from .collect import collect
from .config import DATA_DIR, REPORTS_DIR, load_scoring, load_sources
from .github_client import GitHubClient
from .history import recently_seen
from .publish import publish
from .score import rank


HELP_TEXT = f"""scout {__version__} - daily GitHub repo shortlist

Usage:
  scout [COMMAND] [OPTIONS]

Commands:
  run        Build today's shortlist and print it. (default)
             Options: --date YYYY-MM-DD
  approve    Walk a shortlist and star the repos you like.
             Use `.` (or no argument) to pick the latest report.
  show       Reprint a saved report (defaults to latest).
  list       List saved reports with their repo counts.
  version    Print the installed version.
  help       Show this help.

Config and output live under ~/.scout (override with SCOUT_HOME).
"""


def _print_file(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    sys.stdout.write(text)
    if not text.endswith("\n"):
        sys.stdout.write("\n")


def _latest_report() -> Path | None:
    if not REPORTS_DIR.exists():
        return None
    candidates = sorted(REPORTS_DIR.glob("*.md"))
    return candidates[-1] if candidates else None


def _resolve_report(arg: str | None) -> Path | None:
    if arg is None:
        return _latest_report()
    path = Path(arg)
    if path.exists():
        return path
    candidate = REPORTS_DIR / f"{arg}.md"
    return candidate if candidate.exists() else None


def cmd_run(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(prog="scout run")
    parser.add_argument("--date", help="Use this date instead of now (YYYY-MM-DD, UTC).")
    args = parser.parse_args(argv)

    now = datetime.now(timezone.utc)
    if args.date:
        now = datetime.fromisoformat(args.date).replace(tzinfo=timezone.utc)

    sources = load_sources()
    scoring = load_scoring()

    candidates = collect(sources, GitHubClient(), now=now)

    dedup_window = int(scoring.get("dedup_window_days", 0))
    if dedup_window > 0:
        seen = recently_seen(DATA_DIR, dedup_window, now)
        if seen:
            before = len(candidates)
            candidates = [r for r in candidates if r.get("full_name") not in seen]
            dropped = before - len(candidates)
            if dropped:
                print(
                    f"Dedup: skipped {dropped} repo(s) seen in the last "
                    f"{dedup_window} day(s).",
                    file=sys.stderr,
                )

    ranked = rank(candidates, scoring, now=now)
    shortlist = ranked[: int(scoring.get("shortlist_size", 5))]
    json_path, md_path = publish(shortlist, date=now)

    _print_file(md_path)
    print(
        f"\nSaved {len(shortlist)} repos to {md_path}",
        file=sys.stderr,
    )
    return 0


def cmd_show(argv: list[str]) -> int:
    arg = argv[0] if argv and argv[0] not in ("-h", "--help") else None
    if argv and argv[0] in ("-h", "--help"):
        print("usage: scout show [DATE|PATH]")
        return 0
    report = _resolve_report(arg)
    if report is None:
        print(f"scout: no report found for {arg or 'any date'}.", file=sys.stderr)
        print("Run `scout` first to generate one.", file=sys.stderr)
        return 1
    _print_file(report)
    return 0


def cmd_list(argv: list[str]) -> int:
    if not DATA_DIR.exists():
        print("No reports yet. Run `scout` to generate one.")
        return 0
    rows: list[tuple[str, int]] = []
    for path in sorted(DATA_DIR.glob("*.json")):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            rows.append((path.stem, int(data.get("count", 0))))
        except (OSError, ValueError):
            rows.append((path.stem, -1))
    if not rows:
        print("No reports yet. Run `scout` to generate one.")
        return 0
    print(f"{'DATE':<12}  {'REPOS':>5}")
    for date, count in rows:
        count_str = "?" if count < 0 else str(count)
        print(f"{date:<12}  {count_str:>5}")
    return 0


def _safe_stdio() -> None:
    # Windows consoles default to cp1252 which chokes on emojis in repo
    # descriptions. Force UTF-8 with replacement so terminal output never crashes.
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure:
            try:
                reconfigure(encoding="utf-8", errors="replace")
            except Exception:
                pass


def main(argv: list[str] | None = None) -> int:
    _safe_stdio()
    argv = list(sys.argv[1:] if argv is None else argv)

    if not argv:
        return cmd_run([])

    head = argv[0]

    if head in ("-h", "--help", "help"):
        print(HELP_TEXT)
        return 0
    if head in ("-V", "--version", "version"):
        print(f"scout {__version__}")
        return 0
    if head.startswith("-"):
        return cmd_run(argv)

    rest = argv[1:]
    if head == "run":
        return cmd_run(rest)
    if head == "approve":
        return approve_main(rest)
    if head == "show":
        return cmd_show(rest)
    if head == "list":
        return cmd_list(rest)

    print(f"scout: unknown command '{head}'\n", file=sys.stderr)
    print(HELP_TEXT)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
