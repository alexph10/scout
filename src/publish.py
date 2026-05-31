"""Write the shortlist as JSON and Markdown."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .config import DATA_DIR, REPORTS_DIR


def _slim(repo: dict[str, Any]) -> dict[str, Any]:
    return {
        "full_name": repo.get("full_name"),
        "html_url": repo.get("html_url"),
        "description": repo.get("description"),
        "language": repo.get("language"),
        "topics": repo.get("topics") or [],
        "stargazers_count": repo.get("stargazers_count"),
        "pushed_at": repo.get("pushed_at"),
        "source": repo.get("_source"),
        "score": repo.get("_score"),
    }


def write_json(shortlist: list[dict[str, Any]], date: datetime) -> Path:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    path = DATA_DIR / f"{date.date().isoformat()}.json"
    payload = {
        "generated_at": date.isoformat(),
        "count": len(shortlist),
        "repos": [_slim(r) for r in shortlist],
    }
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return path


def write_markdown(shortlist: list[dict[str, Any]], date: datetime) -> Path:
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    path = REPORTS_DIR / f"{date.date().isoformat()}.md"

    lines: list[str] = []
    lines.append(f"# Daily GitHub Shortlist: {date.date().isoformat()}")
    lines.append("")
    lines.append(f"_Generated {date.isoformat()}_")
    lines.append("")
    if not shortlist:
        lines.append("_No repos matched the configured sources today._")
        path.write_text("\n".join(lines), encoding="utf-8")
        return path

    for idx, repo in enumerate(shortlist, start=1):
        score = repo.get("_score", {})
        topics = ", ".join((repo.get("topics") or [])[:5]) or "n/a"
        lines.append(
            f"## {idx}. [{repo['full_name']}]({repo['html_url']}) "
            f"(score {score.get('total', 0):.3f})"
        )
        if repo.get("description"):
            lines.append("")
            lines.append(f"> {repo['description']}")
        lines.append("")
        lines.append(
            f"- {repo.get('stargazers_count', 0):,} stars, "
            f"language: `{repo.get('language') or 'n/a'}`, "
            f"pushed: {repo.get('pushed_at', 'n/a')}"
        )
        lines.append(f"- topics: {topics}")
        lines.append(
            f"- source: `{repo.get('_source', 'n/a')}`, "
            f"activity {score.get('activity', 0):.2f}, "
            f"popularity {score.get('popularity', 0):.2f}, "
            f"language {score.get('language', 0):.2f}, "
            f"topic {score.get('topic', 0):.2f}"
        )
        lines.append("")

    lines.append("---")
    lines.append("")
    lines.append("Run `scout approve .` to star approved repos.")
    lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")
    return path


def publish(shortlist: list[dict[str, Any]], date: datetime | None = None) -> tuple[Path, Path]:
    date = date or datetime.now(timezone.utc)
    return write_json(shortlist, date), write_markdown(shortlist, date)
