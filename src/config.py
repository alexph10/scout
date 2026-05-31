"""Paths and YAML loaders.

Scout reads config and writes data under SCOUT_HOME (default ~/.scout).
On first use the bundled defaults are copied there so the user can edit them.
"""

from __future__ import annotations

import os
import shutil
from pathlib import Path
from typing import Any

import yaml


def _scout_home() -> Path:
    env = os.environ.get("SCOUT_HOME")
    if env:
        return Path(env).expanduser().resolve()
    return Path.home() / ".scout"


SCOUT_HOME = _scout_home()
CONFIG_DIR = SCOUT_HOME / "config"
DATA_DIR = SCOUT_HOME / "data"
REPORTS_DIR = SCOUT_HOME / "reports"
ENV_FILE = SCOUT_HOME / ".env"

_DEFAULTS_DIR = Path(__file__).resolve().parent / "_defaults"


def _ensure_config(name: str) -> Path:
    """Return the user config path, copying the bundled default if missing."""
    target = CONFIG_DIR / name
    if not target.exists():
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        shutil.copy(_DEFAULTS_DIR / name, target)
    return target


def load_yaml(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def load_sources() -> dict[str, Any]:
    return load_yaml(_ensure_config("sources.yml"))


def load_scoring() -> dict[str, Any]:
    return load_yaml(_ensure_config("scoring.yml"))


def load_dotenv(path: Path | None = None, override: bool = False) -> dict[str, str]:
    """Load KEY=VALUE pairs from a .env file into os.environ.

    Existing environment variables win unless override=True. Returns the dict
    of keys read from the file. Silently no-ops if the file does not exist.
    """
    path = path or ENV_FILE
    loaded: dict[str, str] = {}
    if not path.exists():
        return loaded

    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line[len("export "):].lstrip()
        if "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in ("'", '"'):
            value = value[1:-1]
        if not key:
            continue
        loaded[key] = value
        if override or key not in os.environ:
            os.environ[key] = value
    return loaded
