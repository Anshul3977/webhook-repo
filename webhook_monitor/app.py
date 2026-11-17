"""Flask application factory."""

from __future__ import annotations

import hmac
import logging
from pathlib import Path

from flask import Flask, jsonify, render_template, request
from pymongo.errors import PyMongoError
from werkzeug.exceptions import HTTPException

from webhook_monitor.config import Settings
from webhook_monitor.db import Database
from webhook_monitor.errors import error_response
from webhook_monitor.formatting import format_message
from webhook_monitor.ingest import accept_event, replay_demo, seed_demo_if_enabled
from webhook_monitor.parsing import PayloadError, normalize_timestamp
from webhook_monitor.signatures import verify_signature

logger = logging.getLogger("webhook_monitor")

ROOT = Path(__file__).resolve().parent.parent
_ACTIONS = {"push", "pull_request", "merge"}
_JSON_CONTENT_TYPE = "application/json"


def create_app(settings: Settings | None = None) -> Flask:
    settings = settings or Settings.from_env()
    _configure_logging(settings.log_level)

    app = Flask(__name__, template_folder=str(ROOT / "templates"))
    app.config["MAX_CONTENT_LENGTH"] = settings.max_body_bytes
    app.config["SETTINGS"] = settings
    database = Database(settings)
    app.config["DATABASE"] = database
    seed_demo_if_enabled(database)

    @app.get("/")
    def index():
        return render_template("index.html", demo_mode=settings.demo_mode, poll_seconds=15)

    @app.get("/health")
    def health():
        # The process is healthy even when MongoDB is briefly unreachable.
        # Failing this check would make Render restart the instance, which
        # does not repair an Atlas network or credential problem.
        database_status = "ok" if database.ping() else "unavailable"
        return jsonify({"status": "healthy", "database": database_status}), 200

    @app.post("/webhook")
    def webhook():
        if not settings.webhook_secret:
            logger.error("webhook_rejected code=webhook_not_configured")
            return error_response(
                "webhook_not_configured",
                "WEBHOOK_SECRET is not set.",
                503,
            )

        body = request.get_data(cache=True) or b""
        signature = request.headers.get("X-Hub-Signature-256")
        if not verify_signature(settings.webhook_secret, body, signature):
            logger.warning("webhook_rejected code=invalid_signature")
            return error_response(
                "invalid_signature",
                "The webhook signature is missing or invalid.",
                401,
            )

        content_type = (request.content_type or "").split(";", 1)[0].strip().lower()
        if content_type != _JSON_CONTENT_TYPE:
            return error_response(
                "invalid_content_type",
                "Content-Type must be application/json.",
                400,
            )

        payload = request.get_json(silent=True)
        if payload is None:
            return error_response("invalid_json", "Request body is not valid JSON.", 400)

        event_type = request.headers.get("X-GitHub-Event", "")
        if event_type == "ping":
            return jsonify({"status": "ok", "event": "ping"}), 200

        delivery_id = request.headers.get("X-GitHub-Delivery")
        try:
            result = accept_event(
                database,
                event_type=event_type,
                delivery_id=delivery_id or "",
                payload=payload,
                source="github",
            )
        except PayloadError as exc:
            logger.warning("webhook_rejected code=invalid_payload")
            return error_response("invalid_payload", exc.message, 400)
        except PyMongoError:
            logger.warning("webhook_rejected code=database_unavailable")
            return error_response(
                "database_unavailable",
                "The event store is unavailable.",
                503,
            )
        return jsonify(result), 200

    @app.get("/events")
    def list_events():
        try:
            limit = _parse_limit(request.args.get("limit"))
            action = _parse_action(request.args.get("action"))
            since = _parse_since(request.args.get("since") or request.args.get("last_timestamp"))
        except PayloadError as exc:
            return error_response("invalid_query", exc.message, 400)

        query: dict = {}
        if action:
            query["action"] = action
        if since:
            query["timestamp"] = {"$gt": since}

        try:
            database.ensure()
            rows = list(
                database.collection.find(query, {"_id": 0}).sort("timestamp", -1).limit(limit)
            )
        except PyMongoError:
            logger.warning("events_list_failed")
            return error_response(
                "database_unavailable",
                "The event store is unavailable.",
                503,
            )

        events = []
        for row in rows:
            try:
                message = format_message(row)
            except (KeyError, ValueError):
                logger.warning("event_skipped delivery_id=%s", row.get("delivery_id"))
                continue
            events.append(
                {
                    "message": message,
                    "timestamp": row.get("timestamp"),
                    "action": row.get("action"),
                    "author": row.get("author"),
                    "from_branch": row.get("from_branch"),
                    "to_branch": row.get("to_branch"),
                    "request_id": row.get("request_id"),
                    "delivery_id": row.get("delivery_id"),
                    "repository": row.get("repository"),
                    "source": row.get("source", "github"),
                }
            )
        return jsonify({"events": events}), 200

    @app.post("/demo/replay")
    def demo_replay():
        if not _demo_allowed(settings):
            return error_response(
                "demo_unauthorized",
                "Demo replay is disabled. Set DEMO_MODE=true or send a valid X-Demo-Token.",
                401,
            )
        try:
            results = replay_demo(database)
        except PyMongoError:
            logger.warning("demo_replay_failed")
            return error_response(
                "database_unavailable",
                "The event store is unavailable.",
                503,
            )
        return jsonify({"status": "ok", "results": results}), 200

    @app.errorhandler(HTTPException)
    def http_error(exc: HTTPException):
        messages = {
            404: ("not_found", "No route matches this path."),
            405: ("method_not_allowed", "This route does not accept that method."),
            413: ("payload_too_large", "Request body exceeds the 1 MB limit."),
        }
        code, message = messages.get(exc.code or 500, ("http_error", "Request failed."))
        return error_response(code, message, exc.code or 500)

    @app.errorhandler(Exception)
    def unexpected_error(exc: Exception):
        if isinstance(exc, HTTPException):
            return http_error(exc)
        logger.exception("unhandled_error")
        return error_response(
            "internal_error",
            "The server could not complete the request.",
            500,
        )

    return app


def _demo_allowed(settings: Settings) -> bool:
    if settings.demo_mode:
        return True
    provided = request.headers.get("X-Demo-Token", "")
    expected = settings.demo_token
    if not provided or not expected or len(provided) != len(expected):
        return False
    return hmac.compare_digest(provided, expected)


def _parse_limit(raw: str | None) -> int:
    if raw is None or raw == "":
        return 50
    if not raw.isdigit():
        raise PayloadError("limit must be an integer from 1 to 100.")
    value = int(raw)
    if value < 1 or value > 100:
        raise PayloadError("limit must be an integer from 1 to 100.")
    return value


def _parse_action(raw: str | None) -> str | None:
    if raw is None or raw == "":
        return None
    if raw not in _ACTIONS:
        raise PayloadError("action must be push, pull_request, or merge.")
    return raw


def _parse_since(raw: str | None) -> str | None:
    if raw is None or raw == "":
        return None
    return normalize_timestamp(raw, field="since")


def _configure_logging(level_name: str) -> None:
    level = getattr(logging, level_name.upper(), logging.INFO)
    logger.setLevel(level)
    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(name)s %(message)s"))
        logger.addHandler(handler)
    logger.propagate = False
