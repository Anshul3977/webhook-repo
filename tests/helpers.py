"""HTTP helpers shared by webhook tests."""

from __future__ import annotations

import json

from webhook_monitor.signatures import sign_body


def post_webhook(
    client,
    secret: str,
    event: str,
    payload: dict,
    delivery: str,
    *,
    signature: str | None | bool = None,
    content_type: str = "application/json",
    raw: bytes | None = None,
):
    body = raw if raw is not None else json.dumps(payload, separators=(",", ":")).encode()
    headers = {
        "Content-Type": content_type,
        "X-GitHub-Event": event,
        "X-GitHub-Delivery": delivery,
    }
    if signature is not False:
        headers["X-Hub-Signature-256"] = signature or sign_body(secret, body)
    return client.post("/webhook", data=body, headers=headers)
