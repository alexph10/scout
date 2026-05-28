"""Config loading helpers."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
CONFIG_DIR = REPO_ROOT / "config"
DATA_DIR = REPO_ROOT / "data"
REPORTS_DIR = REPO_ROOT / "reports"


def load_yaml(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def load_sources() -> dict[str, Any]:
    return load_yaml(CONFIG_DIR / "sources.yml")


def load_scoring() -> dict[str, Any]:
    return load_yaml(CONFIG_DIR / "scoring.yml")
