"""Shared pytest fixtures. Each test gets a fresh mongomock database."""

from __future__ import annotations

import pytest
from webhook_monitor.app import create_app
from webhook_monitor.config import Settings


@pytest.fixture
def settings() -> Settings:
    return Settings(
        mongo_uri="mongomock://localhost",
        mongo_db="github_events_test",
        mongo_collection="events",
        webhook_secret="test-secret",
        demo_mode=False,
        demo_token="demo-token",
        log_level="WARNING",
    )


@pytest.fixture
def client(settings):
    application = create_app(settings)
    application.config["TESTING"] = True
    return application.test_client()
