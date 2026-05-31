"""Small GitHub REST client."""

from __future__ import annotations

import os
import shutil
import subprocess
import time
from typing import Any

import requests

API_ROOT = "https://api.github.com"
USER_AGENT = "daily-github-shortlist/0.1"
REQUEST_TIMEOUT = 15  # seconds


def _gh_cli_token() -> str | None:
    """Fall back to the GitHub CLI (`gh auth token`) if it's installed and logged in."""
    if not shutil.which("gh"):
        return None
    try:
        result = subprocess.run(
            ["gh", "auth", "token"],
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    if result.returncode != 0:
        return None
    token = result.stdout.strip()
    return token or None


def detect_token() -> str | None:
    """Try GITHUB_TOKEN, then GH_TOKEN, then `gh auth token`."""
    for var in ("GITHUB_TOKEN", "GH_TOKEN"):
        val = os.environ.get(var)
        if val:
            return val
    return _gh_cli_token()


class GitHubClient:
    def __init__(self, token: str | None = None, session: requests.Session | None = None):
        self.token = token if token is not None else detect_token()
        self.session = session or requests.Session()
        self.session.headers.update(
            {
                "Accept": "application/vnd.github+json",
                "X-GitHub-Api-Version": "2022-11-28",
                "User-Agent": USER_AGENT,
            }
        )
        if self.token:
            self.session.headers["Authorization"] = f"Bearer {self.token}"

    def search_repositories(
        self,
        q: str,
        sort: str = "stars",
        order: str = "desc",
        per_page: int = 30,
    ) -> list[dict[str, Any]]:
        resp = self._get(
            f"{API_ROOT}/search/repositories",
            params={"q": q, "sort": sort, "order": order, "per_page": per_page},
        )
        return resp.json().get("items", [])

    def get_repository(self, full_name: str) -> dict[str, Any]:
        resp = self._get(f"{API_ROOT}/repos/{full_name}")
        return resp.json()

    def list_starred(self, per_page: int = 100) -> set[str]:
        """Return the full_names of every repo the authenticated user has starred.

        One paginated walk of /user/starred. Returns an empty set if there is no
        token configured.
        """
        if not self.token:
            return set()
        starred: set[str] = set()
        page = 1
        while True:
            resp = self._get(
                f"{API_ROOT}/user/starred",
                params={"per_page": per_page, "page": page},
            )
            items = resp.json()
            if not items:
                break
            for repo in items:
                name = repo.get("full_name")
                if name:
                    starred.add(name)
            if len(items) < per_page:
                break
            page += 1
        return starred

    def is_starred(self, full_name: str) -> bool:
        resp = self.session.get(
            f"{API_ROOT}/user/starred/{full_name}", timeout=REQUEST_TIMEOUT
        )
        if resp.status_code == 204:
            return True
        if resp.status_code == 404:
            return False
        resp.raise_for_status()
        return False

    def star(self, full_name: str) -> None:
        resp = self.session.put(
            f"{API_ROOT}/user/starred/{full_name}", timeout=REQUEST_TIMEOUT
        )
        resp.raise_for_status()

    def _get(self, url: str, params: dict[str, Any] | None = None) -> requests.Response:
        # Retry on rate limit.
        for _ in range(3):
            resp = self.session.get(url, params=params, timeout=REQUEST_TIMEOUT)
            if resp.status_code == 403 and "rate limit" in resp.text.lower():
                reset = int(resp.headers.get("X-RateLimit-Reset", "0"))
                time.sleep(min(max(1, reset - int(time.time())), 60))
                continue
            resp.raise_for_status()
            return resp
        resp.raise_for_status()
        return resp
