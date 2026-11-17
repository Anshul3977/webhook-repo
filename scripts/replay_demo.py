"""Replay bundled sample payloads through a running webhook endpoint.

Signs each body with WEBHOOK_SECRET and posts it to /webhook, which is the
same path GitHub uses. Delivery ids are stable, so running this twice does
not create duplicate rows.

Usage:
    WEBHOOK_SECRET=... python scripts/replay_demo.py
    WEBHOOK_URL=http://localhost:5000/webhook WEBHOOK_SECRET=... python scripts/replay_demo.py
"""

from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.request

from webhook_monitor.demo import load_demo_events
from webhook_monitor.signatures import sign_body


def main() -> int:
    secret = os.environ.get("WEBHOOK_SECRET", "")
    if not secret:
        print("WEBHOOK_SECRET is required.", file=sys.stderr)
        return 1
    url = os.environ.get("WEBHOOK_URL", "http://localhost:5000/webhook")
    failures = 0
    for item in load_demo_events():
        body = json.dumps(item.payload, separators=(",", ":")).encode("utf-8")
        request = urllib.request.Request(
            url,
            data=body,
            method="POST",
            headers={
                "Content-Type": "application/json",
                "X-GitHub-Event": item.event_type,
                "X-GitHub-Delivery": item.delivery_id,
                "X-Hub-Signature-256": sign_body(secret, body),
                "User-Agent": "webhook-monitor-demo",
            },
        )
        try:
            with urllib.request.urlopen(request, timeout=15) as response:
                status = response.status
                payload = response.read().decode("utf-8")
        except urllib.error.HTTPError as exc:
            status = exc.code
            payload = exc.read().decode("utf-8")
            failures += 1
        except urllib.error.URLError as exc:
            print(f"{item.delivery_id} failed: {exc.reason}", file=sys.stderr)
            failures += 1
            continue
        print(f"{item.delivery_id} {status} {payload}")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
