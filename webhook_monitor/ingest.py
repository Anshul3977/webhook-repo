"""Store a validated event once per GitHub delivery id."""

from __future__ import annotations

import logging

from pymongo.errors import DuplicateKeyError

from webhook_monitor.db import Database
from webhook_monitor.demo import load_demo_events
from webhook_monitor.parsing import IgnoredEvent, parse_event, validate_delivery_id

logger = logging.getLogger("webhook_monitor")


def accept_event(
    db: Database,
    *,
    event_type: str,
    delivery_id: str,
    payload: object,
    source: str,
) -> dict:
    """Validate and insert one event.

    Duplicate deliveries return status=duplicate and do not insert a second row.
    Events this service does not track return status=ignored.
    """
    delivery_id = validate_delivery_id(delivery_id)
    try:
        parsed = parse_event(event_type, payload)
    except IgnoredEvent as exc:
        logger.info(
            "event_ignored delivery_id=%s event_type=%s reason=%s",
            delivery_id,
            event_type,
            exc.reason,
        )
        return {"status": "ignored", "reason": exc.reason, "delivery_id": delivery_id}

    document = parsed.to_document(delivery_id=delivery_id, source=source)
    db.ensure()
    try:
        db.collection.insert_one(document)
    except DuplicateKeyError:
        logger.info("event_duplicate delivery_id=%s action=%s", delivery_id, document["action"])
        return {
            "status": "duplicate",
            "delivery_id": delivery_id,
            "action": document["action"],
        }
    logger.info(
        "event_stored delivery_id=%s action=%s source=%s",
        delivery_id,
        document["action"],
        source,
    )
    return {"status": "stored", "delivery_id": delivery_id, "action": document["action"]}


def replay_demo(db: Database) -> list[dict]:
    """Insert the bundled fixtures. Safe to call more than once."""
    db.ensure()
    results = []
    for item in load_demo_events():
        results.append(
            accept_event(
                db,
                event_type=item.event_type,
                delivery_id=item.delivery_id,
                payload=item.payload,
                source="demo",
            )
        )
    return results


def seed_demo_if_enabled(db: Database) -> None:
    if not db.settings.demo_mode:
        return
    try:
        results = replay_demo(db)
    except Exception as exc:
        logger.warning("demo_seed_skipped error_type=%s", type(exc).__name__)
        return
    stored = sum(1 for item in results if item.get("status") == "stored")
    logger.info("demo_seed_complete stored=%s total=%s", stored, len(results))
