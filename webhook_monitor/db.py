"""MongoDB access. Tests pass a mongomock URI; production uses MONGO_URI."""

from __future__ import annotations

import logging

from pymongo import DESCENDING, MongoClient

from webhook_monitor.config import Settings

logger = logging.getLogger("webhook_monitor")


class Database:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.client = _client(settings)
        self.collection = self.client[settings.mongo_db][settings.mongo_collection]
        self._ready = False

    def ensure(self) -> None:
        if self._ready:
            return
        self.collection.create_index("delivery_id", unique=True, name="delivery_id_unique")
        self.collection.create_index([("timestamp", DESCENDING)], name="timestamp_desc")
        self._ready = True

    def ping(self) -> bool:
        if self.settings.mongo_uri.startswith("mongomock://"):
            return True
        try:
            self.client.admin.command("ping")
        except Exception:
            logger.warning("database_ping_failed")
            return False
        return True


def _client(settings: Settings):
    if settings.mongo_uri.startswith("mongomock://"):
        import mongomock

        return mongomock.MongoClient()
    return MongoClient(
        settings.mongo_uri,
        serverSelectionTimeoutMS=settings.server_selection_timeout_ms,
        connectTimeoutMS=settings.server_selection_timeout_ms,
        connect=False,
    )
