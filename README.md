# daily-github-shortlist

A GitHub repository discovery pipeline that scores projects by activity, stars,
language, and topic match, then publishes a daily top 5 list.

## What it does

Each day the pipeline answers one question: **"What are the top 5 GitHub repos
I should look at today?"**

It runs four stages:

1. **Collect** – query the GitHub Search API and any curated sources defined in
   [`config/sources.yml`](config/sources.yml).
2. **Score** – rank repos with a transparent formula combining recency,
   popularity, language preference, and topic match.
3. **Publish** – write a daily Markdown report to `reports/YYYY-MM-DD.md` and
   the underlying data to `data/YYYY-MM-DD.json`.
4. **Approve** – review the shortlist locally and optionally star approved
   repos via the GitHub REST API. Nothing is starred automatically.

## Project layout

```
daily-github-shortlist/
├── .github/workflows/daily.yml   # scheduled pipeline (cron, UTC)
├── config/
│   ├── sources.yml               # search queries + curated repos
│   └── scoring.yml               # weights and language/topic preferences
├── src/
│   ├── collect.py                # GitHub Search API client
│   ├── score.py                  # scoring rubric
│   ├── publish.py                # markdown + json report writer
│   ├── approve.py                # interactive starring CLI
│   ├── github_client.py          # thin requests wrapper
│   ├── config.py                 # config loader
│   └── pipeline.py               # orchestrates collect → score → publish
├── data/                         # daily JSON snapshots
├── reports/                      # daily markdown shortlists
├── tests/
└── requirements.txt
```

## Quick start

```bash
python -m venv .venv
.venv\Scripts\activate            # Windows
pip install -r requirements.txt

# Run the daily pipeline
$env:GITHUB_TOKEN = "ghp_..."
python -m src.pipeline

# Review and star approved repos interactively
python -m src.approve reports/2026-05-28.md
```

## Configuration

Edit [`config/sources.yml`](config/sources.yml) to add GitHub search queries or
pin curated repos. Edit [`config/scoring.yml`](config/scoring.yml) to tune the
scoring weights, preferred languages, and topic boosts.

## Scheduling

The workflow in [`.github/workflows/daily.yml`](.github/workflows/daily.yml)
runs every day at 13:00 UTC, generates the report, and commits it back to the
repo. Starring stays manual — the workflow never calls the star endpoint.

## License

MIT
