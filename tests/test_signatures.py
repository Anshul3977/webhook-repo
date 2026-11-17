"""Signature verification, including the HTTP boundary."""

import json
from dataclasses import replace

from tests.helpers import post_webhook
from webhook_monitor.app import create_app
from webhook_monitor.signatures import sign_body, verify_signature

SECRET = "test-secret"
PUSH = {
    "ref": "refs/heads/main",
    "pusher": {"name": "Anshul3977"},
    "head_commit": {
        "id": "a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2",
        "timestamp": "2026-01-29T16:48:00Z",
    },
}


def test_known_hmac_vector():
    body = b'{"zen":"design for operation"}'
    expected = sign_body("secret", body)
    assert expected.startswith("sha256=")
    assert len(expected) == len("sha256=") + 64
    assert verify_signature("secret", body, expected) is True
    assert verify_signature("secret", body, expected.upper()) is False
    assert verify_signature("", body, expected) is False
    assert verify_signature("secret", body, None) is False


def test_valid_signature_is_accepted(client):
    response = post_webhook(client, SECRET, "push", PUSH, "delivery-push-01")
    assert response.status_code == 200
    assert response.get_json()["status"] == "stored"


def test_missing_signature_is_rejected(client):
    response = post_webhook(client, SECRET, "push", PUSH, "delivery-push-02", signature=False)
    assert response.status_code == 401
    body = response.get_json()
    assert body["error"]["code"] == "invalid_signature"
    assert client.get("/events").get_json()["events"] == []


def test_wrong_secret_is_rejected(client):
    body = json.dumps(PUSH, separators=(",", ":")).encode()
    response = post_webhook(
        client,
        SECRET,
        "push",
        PUSH,
        "delivery-push-03",
        signature=sign_body("other-secret", body),
        raw=body,
    )
    assert response.status_code == 401
    assert client.get("/events").get_json()["events"] == []


def test_tampered_body_is_rejected(client):
    body = json.dumps(PUSH, separators=(",", ":")).encode()
    signature = sign_body(SECRET, body)
    tampered = body.replace(b"main", b"prod")
    response = post_webhook(
        client,
        SECRET,
        "push",
        PUSH,
        "delivery-push-04",
        signature=signature,
        raw=tampered,
    )
    assert response.status_code == 401


def test_missing_webhook_secret_fails_closed(settings):
    application = create_app(replace(settings, webhook_secret=""))
    local = application.test_client()
    response = post_webhook(local, "anything", "push", PUSH, "delivery-push-05")
    assert response.status_code == 503
    assert response.get_json()["error"]["code"] == "webhook_not_configured"
