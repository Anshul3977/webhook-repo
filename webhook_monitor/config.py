"""Runtime settings loaded from the environment."""

from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv

_TRUE = {"1", "true", "yes", "on"}


def as_bool(value: str | None, default: bool = False) -> bool:
    """Parse an env-var boolean. Only explicit true-like strings enable a flag."""
    if value is None or value.strip() == "":
        return default
    return value.strip().lower() in _TRUE


@dataclass(frozen=True)
class Settings:
    mongo_uri: str
    mongo_db: str
    mongo_collection: str
    webhook_secret: str
    demo_mode: bool
    demo_token: str
    log_level: str
    server_selection_timeout_ms: int = 2000
    max_body_bytes: int = 1_000_000

    @classmethod
    def from_env(cls) -> Settings:
        # Existing process env wins over a local .env file.
        load_dotenv(override=False)
        timeout_raw = os.getenv("MONGO_SERVER_SELECTION_TIMEOUT_MS", "2000")
        try:
            timeout_ms = int(timeout_raw)
        except ValueError:
            timeout_ms = 2000
        timeout_ms = min(max(timeout_ms, 200), 10000)
        return cls(
            mongo_uri=os.getenv("MONGO_URI", "mongodb://localhost:27017/"),
            mongo_db=os.getenv("MONGO_DB", "github_events"),
            mongo_collection=os.getenv("MONGO_COLLECTION", "events"),
            webhook_secret=os.getenv("WEBHOOK_SECRET", ""),
            demo_mode=as_bool(os.getenv("DEMO_MODE"), False),
            demo_token=os.getenv("DEMO_TOKEN", ""),
            log_level=os.getenv("LOG_LEVEL", "INFO"),
            server_selection_timeout_ms=timeout_ms,
        )
