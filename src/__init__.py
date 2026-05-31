"""Daily GitHub shortlist pipeline."""

from .config import load_dotenv

__version__ = "0.2.0"

# Pick up GITHUB_TOKEN from ~/.scout/.env without requiring shell setup.
# Real environment variables always win.
load_dotenv()
