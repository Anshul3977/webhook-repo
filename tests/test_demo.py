"""Demo replay inserts only the bundled fixtures, and only once."""

from webhook_monitor.app import create_app
from webhook_monitor.config import Settings
from webhook_monitor.demo import load_demo_events


def _settings(**overrides) -> Settings:
    values = {
        "mongo_uri": "mongomock://localhost",
        "mongo_db": "github_events_test",
        "mongo_collection": "events",
        "webhook_secret": "test-secret",
        "demo_mode": False,
        "demo_token": "demo-token",
        "log_level": "WARNING",
    }
    values.update(overrides)
    return Settings(**values)


def test_fixtures_cover_each_event_type():
    events = load_demo_events()
    assert len(events) == 3
    assert {item.event_type for item in events} == {"push", "pull_request"}
    actions = {item.payload.get("action") for item in events}
    assert "opened" in actions
    assert "closed" in actions


def test_replay_requires_demo_mode_or_token():
    application = create_app(_settings(demo_mode=False, demo_token="demo-token"))
    client = application.test_client()
    denied = client.post("/demo/replay")
    assert denied.status_code == 401
    assert denied.get_json()["error"]["code"] == "demo_unauthorized"
    assert client.get("/events").get_json()["events"] == []

    allowed = client.post("/demo/replay", headers={"X-Demo-Token": "demo-token"})
    assert allowed.status_code == 200
    events = client.get("/events").get_json()["events"]
    assert {event["action"] for event in events} == {"push", "pull_request", "merge"}
    assert {event["source"] for event in events} == {"demo"}


def test_replay_is_idempotent_and_public_in_demo_mode():
    application = create_app(_settings(demo_mode=True))
    client = application.test_client()
    seeded = client.get("/events").get_json()["events"]
    assert len(seeded) == 3

    page = client.get("/")
    assert b"Replay sample events" in page.data
    assert b"sample" in page.data

    again = client.post("/demo/replay")
    assert again.status_code == 200
    assert all(item["status"] == "duplicate" for item in again.get_json()["results"])
    assert len(client.get("/events").get_json()["events"]) == 3


def test_wrong_demo_token_does_not_insert():
    application = create_app(_settings(demo_mode=False, demo_token="demo-token"))
    client = application.test_client()
    response = client.post("/demo/replay", headers={"X-Demo-Token": "nope"})
    assert response.status_code == 401
    assert client.get("/events").get_json()["events"] == []
