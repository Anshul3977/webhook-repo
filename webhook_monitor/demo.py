"""Bundled sample payloads used by demo mode and scripts/replay_demo.py."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

SAMPLES_DIR = Path(__file__).resolve().parent.parent / "samples"


@dataclass(frozen=True)
class DemoDelivery:
    event_type: str
    delivery_id: str
    payload: dict


def load_demo_events() -> list[DemoDelivery]:
    manifest = json.loads((SAMPLES_DIR / "manifest.json").read_text(encoding="utf-8"))
    events: list[DemoDelivery] = []
    for item in manifest:
        payload = json.loads((SAMPLES_DIR / item["file"]).read_text(encoding="utf-8"))
        events.append(
            DemoDelivery(
                event_type=item["event"],
                delivery_id=item["delivery_id"],
                payload=payload,
            )
        )
    return events
