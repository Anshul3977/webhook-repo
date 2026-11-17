"""Push, pull request, and merge ingestion."""

from tests.helpers import post_webhook

SECRET = "test-secret"
SHA = "a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2"


def _push(ref="refs/heads/feature/dashboard"):
    return {
        "ref": ref,
        "repository": {"full_name": "Anshul3977/webhook-repo"},
        "pusher": {"name": "Anshul3977"},
        "head_commit": {"id": SHA, "timestamp": "2026-01-29T16:48:00Z"},
    }


def _pull(action="opened", **overrides):
    pull = {
        "id": 42,
        "user": {"login": "Anshul3977"},
        "head": {"ref": "feature/dashboard"},
        "base": {"ref": "main"},
        "created_at": "2026-01-29T16:49:00Z",
        "updated_at": "2026-01-29T17:00:00Z",
        "merged": False,
    }
    pull.update(overrides)
    return {
        "action": action,
        "repository": {"full_name": "Anshul3977/webhook-repo"},
        "pull_request": pull,
    }


def test_push_keeps_slashes_in_the_branch_name(client):
    response = post_webhook(client, SECRET, "push", _push(), "delivery-push-10")
    assert response.status_code == 200
    event = client.get("/events").get_json()["events"][0]
    assert event["action"] == "push"
    assert event["to_branch"] == "feature/dashboard"
    assert event["from_branch"] is None
    assert event["message"] == (
        "Anshul3977 pushed to feature/dashboard on 29th January 2026 - 4:48 PM UTC"
    )
    assert event["repository"] == "Anshul3977/webhook-repo"
    assert event["source"] == "github"


def test_pull_request_opened(client):
    response = post_webhook(client, SECRET, "pull_request", _pull(), "delivery-pr-10")
    assert response.status_code == 200
    assert response.get_json()["action"] == "pull_request"
    event = client.get("/events").get_json()["events"][0]
    assert event["from_branch"] == "feature/dashboard"
    assert event["to_branch"] == "main"
    assert event["message"] == (
        "Anshul3977 submitted a pull request from feature/dashboard to main "
        "on 29th January 2026 - 4:49 PM UTC"
    )


def test_merge_is_a_closed_pull_request(client):
    payload = _pull(
        action="closed",
        merged=True,
        merged_at="2026-01-29T16:50:00Z",
    )
    response = post_webhook(client, SECRET, "pull_request", payload, "delivery-merge-10")
    assert response.status_code == 200
    assert response.get_json()["action"] == "merge"
    event = client.get("/events").get_json()["events"][0]
    assert event["action"] == "merge"
    assert event["message"] == (
        "Anshul3977 merged branch feature/dashboard to main on 29th January 2026 - 4:50 PM UTC"
    )


def test_closed_unmerged_pull_request_is_ignored(client):
    response = post_webhook(
        client,
        SECRET,
        "pull_request",
        _pull(action="closed", merged=False),
        "delivery-pr-closed",
    )
    assert response.status_code == 200
    assert response.get_json()["status"] == "ignored"
    assert response.get_json()["reason"] == "pull_request_closed_unmerged"
    assert client.get("/events").get_json()["events"] == []


def test_labeled_pull_request_is_ignored(client):
    response = post_webhook(
        client, SECRET, "pull_request", _pull(action="labeled"), "delivery-pr-label"
    )
    assert response.get_json()["status"] == "ignored"
    assert client.get("/events").get_json()["events"] == []


def test_ping_is_acknowledged(client):
    response = post_webhook(
        client,
        SECRET,
        "ping",
        {"zen": "keep it logically awesome"},
        "delivery-ping",
    )
    assert response.status_code == 200
    assert response.get_json()["event"] == "ping"
    assert client.get("/events").get_json()["events"] == []


def test_invalid_push_payload_is_a_structured_error(client):
    response = post_webhook(
        client,
        SECRET,
        "push",
        {"ref": "refs/heads/main", "pusher": {"name": "Anshul3977"}},
        "delivery-bad-push",
    )
    assert response.status_code == 400
    body = response.get_json()
    assert body["error"]["code"] == "invalid_payload"
    assert "Traceback" not in response.get_data(as_text=True)
    assert client.get("/events").get_json()["events"] == []


def test_branch_delete_is_ignored(client):
    payload = _push()
    payload["head_commit"] = None
    response = post_webhook(client, SECRET, "push", payload, "delivery-delete")
    assert response.status_code == 200
    assert response.get_json()["reason"] == "branch_delete"


def test_timestamp_with_offset_is_stored_in_utc(client):
    payload = _push("refs/heads/main")
    payload["head_commit"]["timestamp"] = "2026-01-29T11:48:00-05:00"
    post_webhook(client, SECRET, "push", payload, "delivery-offset")
    event = client.get("/events").get_json()["events"][0]
    assert event["timestamp"] == "2026-01-29T16:48:00Z"
    assert "4:48 PM UTC" in event["message"]
