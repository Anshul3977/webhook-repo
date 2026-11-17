"""The same X-GitHub-Delivery is stored once."""

from tests.helpers import post_webhook

SECRET = "test-secret"
PAYLOAD = {
    "ref": "refs/heads/main",
    "pusher": {"name": "Anshul3977"},
    "head_commit": {
        "id": "a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2",
        "timestamp": "2026-01-29T16:48:00Z",
    },
}


def test_duplicate_delivery_does_not_insert_twice(client):
    first = post_webhook(client, SECRET, "push", PAYLOAD, "delivery-same")
    second = post_webhook(client, SECRET, "push", PAYLOAD, "delivery-same")
    assert first.status_code == 200
    assert first.get_json()["status"] == "stored"
    assert second.status_code == 200
    assert second.get_json()["status"] == "duplicate"
    events = client.get("/events").get_json()["events"]
    assert len(events) == 1
    assert events[0]["delivery_id"] == "delivery-same"


def test_different_deliveries_are_both_stored(client):
    post_webhook(client, SECRET, "push", PAYLOAD, "delivery-one")
    post_webhook(client, SECRET, "push", PAYLOAD, "delivery-two")
    events = client.get("/events").get_json()["events"]
    assert len(events) == 2
    assert {event["delivery_id"] for event in events} == {"delivery-one", "delivery-two"}
