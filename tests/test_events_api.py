"""GET /events query behavior."""

from tests.helpers import post_webhook

SECRET = "test-secret"
SHA = "a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2"


def test_list_is_newest_first_and_filters(client):
    post_webhook(
        client,
        SECRET,
        "push",
        {
            "ref": "refs/heads/main",
            "pusher": {"name": "Anshul3977"},
            "head_commit": {"id": SHA, "timestamp": "2026-01-29T16:48:00Z"},
        },
        "delivery-list-push",
    )
    post_webhook(
        client,
        SECRET,
        "pull_request",
        {
            "action": "opened",
            "pull_request": {
                "id": 7,
                "user": {"login": "Anshul3977"},
                "head": {"ref": "feature/dashboard"},
                "base": {"ref": "main"},
                "created_at": "2026-01-29T16:49:00Z",
                "merged": False,
            },
        },
        "delivery-list-pr",
    )
    post_webhook(
        client,
        SECRET,
        "pull_request",
        {
            "action": "closed",
            "pull_request": {
                "id": 7,
                "user": {"login": "Anshul3977"},
                "head": {"ref": "feature/dashboard"},
                "base": {"ref": "main"},
                "created_at": "2026-01-29T16:49:00Z",
                "merged": True,
                "merged_at": "2026-01-29T16:50:00Z",
            },
        },
        "delivery-list-merge",
    )

    events = client.get("/events").get_json()["events"]
    assert [event["action"] for event in events] == ["merge", "pull_request", "push"]

    merges = client.get("/events?action=merge").get_json()["events"]
    assert len(merges) == 1
    assert merges[0]["action"] == "merge"

    limited = client.get("/events?limit=1").get_json()["events"]
    assert len(limited) == 1
    assert limited[0]["action"] == "merge"

    since = client.get("/events?since=2026-01-29T16:49:00Z").get_json()["events"]
    assert [event["action"] for event in since] == ["merge"]


def test_invalid_list_queries(client):
    for query in ("limit=0", "limit=101", "limit=nope", "action=fork", "since=yesterday"):
        response = client.get(f"/events?{query}")
        assert response.status_code == 400, query
        assert response.get_json()["error"]["code"] == "invalid_query"


def test_dashboard_and_health(client):
    page = client.get("/")
    assert page.status_code == 200
    assert b"GitHub Events Monitor" in page.data
    assert b"Replay sample events" not in page.data

    health = client.get("/health")
    assert health.status_code == 200
    body = health.get_json()
    assert body["status"] == "healthy"
    assert body["database"] == "ok"


def test_unknown_route_is_json(client):
    response = client.get("/missing")
    assert response.status_code == 404
    assert response.get_json()["error"]["code"] == "not_found"
