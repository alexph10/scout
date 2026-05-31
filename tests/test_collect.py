from datetime import datetime, timezone
from typing import Any

from src.collect import collect, passes_filters


def _repo(**overrides: Any) -> dict[str, Any]:
    base = {
        "full_name": "owner/example",
        "html_url": "https://github.com/owner/example",
        "description": "A reasonably descriptive project for testing purposes.",
        "language": "Python",
        "topics": ["ai"],
        "stargazers_count": 1000,
        "pushed_at": "2026-05-01T00:00:00Z",
        "archived": False,
        "fork": False,
    }
    base.update(overrides)
    return base


class FakeClient:
    def __init__(self, search_results: list[dict[str, Any]], repo_lookups: dict[str, dict[str, Any]] | None = None):
        self._search_results = search_results
        self._repo_lookups = repo_lookups or {}
        self.search_calls: list[dict[str, Any]] = []
        self.lookup_calls: list[str] = []

    def search_repositories(self, q: str, sort: str, order: str, per_page: int) -> list[dict[str, Any]]:
        self.search_calls.append({"q": q, "sort": sort, "order": order, "per_page": per_page})
        return list(self._search_results)

    def get_repository(self, full_name: str) -> dict[str, Any]:
        self.lookup_calls.append(full_name)
        return self._repo_lookups[full_name]


NOW = datetime(2026, 5, 31, tzinfo=timezone.utc)


def test_archived_excluded_by_default():
    assert passes_filters(_repo(archived=True), {"exclude_archived": True}) is False


def test_fork_excluded_by_default():
    assert passes_filters(_repo(fork=True), {"exclude_forks": True}) is False


def test_min_description_length_drops_short_descriptions():
    short = _repo(description="too short")
    assert passes_filters(short, {"min_description_length": 20}) is False


def test_min_description_length_handles_null_description():
    assert passes_filters(_repo(description=None), {"min_description_length": 1}) is False


def test_clean_repo_passes_all_filters():
    filters = {"exclude_archived": True, "exclude_forks": True, "min_description_length": 20}
    assert passes_filters(_repo(), filters) is True


def test_filters_can_be_disabled():
    filters = {"exclude_archived": False, "exclude_forks": False, "min_description_length": 0}
    assert passes_filters(_repo(archived=True, fork=True, description=""), filters) is True


def test_collect_applies_filters_to_search_results():
    results = [
        _repo(full_name="keep/good"),
        _repo(full_name="drop/archived", archived=True),
        _repo(full_name="drop/fork", fork=True),
        _repo(full_name="drop/no-desc", description=""),
    ]
    client = FakeClient(search_results=results)
    sources = {
        "defaults": {
            "per_page": 30,
            "max_per_query": 30,
            "filters": {
                "exclude_archived": True,
                "exclude_forks": True,
                "min_description_length": 20,
            },
        },
        "queries": [{"name": "test", "q": "topic:ai pushed:>{seven_days_ago}"}],
    }

    out = collect(sources, client, now=NOW)
    full_names = {r["full_name"] for r in out}
    assert full_names == {"keep/good"}


def test_curated_bypasses_filters():
    # Search returns nothing useful; curated picks an "archived" repo that we still want.
    client = FakeClient(
        search_results=[],
        repo_lookups={"owner/legacy": _repo(full_name="owner/legacy", archived=True)},
    )
    sources = {
        "defaults": {"filters": {"exclude_archived": True}},
        "queries": [],
        "curated": ["owner/legacy"],
    }

    out = collect(sources, client, now=NOW)
    assert [r["full_name"] for r in out] == ["owner/legacy"]
    assert out[0]["_source"] == "curated"


def test_query_placeholders_are_substituted():
    client = FakeClient(search_results=[])
    sources = {
        "queries": [{"name": "q", "q": "pushed:>{seven_days_ago} created:>{thirty_days_ago}"}],
    }
    collect(sources, client, now=NOW)
    sent = client.search_calls[0]["q"]
    assert "2026-05-24" in sent  # seven days before 2026-05-31
    assert "2026-05-01" in sent  # thirty days before
