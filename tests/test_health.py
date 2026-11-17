"""Health stays successful when MongoDB cannot be reached."""

from webhook_monitor.app import create_app
from webhook_monitor.config import Settings


def test_health_reports_database_unavailable_without_failing():
    settings = Settings(
        mongo_uri="mongodb://127.0.0.1:1",
        mongo_db="github_events",
        mongo_collection="events",
        webhook_secret="test-secret",
        demo_mode=False,
        demo_token="",
        log_level="WARNING",
        server_selection_timeout_ms=300,
    )
    application = create_app(settings)
    client = application.test_client()
    response = client.get("/health")
    assert response.status_code == 200
    body = response.get_json()
    assert body["status"] == "healthy"
    assert body["database"] == "unavailable"

    events = client.get("/events")
    assert events.status_code == 503
    assert events.get_json()["error"]["code"] == "database_unavailable"
    application.config["DATABASE"].client.close()
