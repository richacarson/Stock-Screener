"""Configuration for the BTC tracker.

Reads credentials from environment variables, falling back to a `.env` file
in the repo root. All keys are optional — sources without credentials are
simply skipped.
"""

import json
import os
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = REPO_ROOT / "data"
PRIVATE_DIR = REPO_ROOT / "private"
TRANSACTIONS_FILE = DATA_DIR / "btc_transactions.json"
MANUAL_FILE = DATA_DIR / "btc_manual.json"
DASHBOARD_FILE = PRIVATE_DIR / "btc_dashboard.html"


def _load_dotenv(path: Path) -> dict[str, str]:
    """Parse a simple KEY=VALUE .env file (no shell interpolation)."""
    env: dict[str, str] = {}
    if not path.exists():
        return env
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        value = value.strip().strip("'\"")
        env[key.strip()] = value
    return env


def get_env(key: str, default: str = "") -> str:
    """Environment variable, falling back to .env in the repo root."""
    if key in os.environ:
        return os.environ[key]
    return _load_dotenv(REPO_ROOT / ".env").get(key, default)


def kraken_credentials() -> tuple[str, str] | None:
    key = get_env("KRAKEN_API_KEY")
    secret = get_env("KRAKEN_API_SECRET")
    return (key, secret) if key and secret else None


def coinbase_credentials() -> tuple[str, str] | None:
    """Return (key_name, private_key_pem) for a Coinbase CDP API key.

    Supports either COINBASE_KEY_FILE (path to the cdp_api_key.json downloaded
    from Coinbase) or COINBASE_API_KEY_NAME + COINBASE_API_PRIVATE_KEY
    (PEM with literal \\n escapes allowed).
    """
    key_file = get_env("COINBASE_KEY_FILE")
    if key_file:
        path = Path(key_file).expanduser()
        if path.exists():
            data = json.loads(path.read_text())
            name = data.get("name") or data.get("id", "")
            pem = data.get("privateKey") or data.get("private_key", "")
            if name and pem:
                return name, pem
    name = get_env("COINBASE_API_KEY_NAME")
    pem = get_env("COINBASE_API_PRIVATE_KEY").replace("\\n", "\n")
    return (name, pem) if name and pem else None


def phantom_addresses() -> list[str]:
    raw = get_env("PHANTOM_BTC_ADDRESSES")
    return [a.strip() for a in raw.split(",") if a.strip()]
