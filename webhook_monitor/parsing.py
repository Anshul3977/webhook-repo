"""Validate GitHub webhook payloads and map them to stored events."""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import UTC, datetime

_COMMIT_ID = re.compile(r"^[0-9a-fA-F]{7,64}$")
_DELIVERY_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{7,127}$")
_STORED_PULL_ACTIONS = {"opened", "reopened"}


class PayloadError(Exception):
    """The payload is a known event type but does not match the required shape."""

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


class IgnoredEvent(Exception):
    """A genuine GitHub event this service intentionally does not store."""

    def __init__(self, reason: str) -> None:
        super().__init__(reason)
        self.reason = reason


@dataclass(frozen=True)
class ParsedEvent:
    author: str
    action: str
    to_branch: str
    from_branch: str | None
    timestamp: str
    request_id: str
    repository: str | None

    def to_document(self, *, delivery_id: str, source: str) -> dict:
        return {
            "author": self.author,
            "action": self.action,
            "to_branch": self.to_branch,
            "from_branch": self.from_branch,
            "timestamp": self.timestamp,
            "request_id": self.request_id,
            "delivery_id": delivery_id,
            "repository": self.repository,
            "source": source,
        }


def validate_delivery_id(delivery_id: str | None) -> str:
    if not isinstance(delivery_id, str) or _DELIVERY_ID.fullmatch(delivery_id) is None:
        raise PayloadError("X-GitHub-Delivery is missing or invalid.")
    return delivery_id


def parse_event(event_type: str, payload: object) -> ParsedEvent:
    if not isinstance(payload, dict):
        raise PayloadError("Payload must be a JSON object.")
    if event_type == "push":
        return _parse_push(payload)
    if event_type == "pull_request":
        return _parse_pull_request(payload)
    raise IgnoredEvent("unsupported_event")


def _text(value: object, *, field: str, max_len: int) -> str:
    if not isinstance(value, str):
        raise PayloadError(f"{field} must be a string.")
    text = value.strip()
    if not text or len(text) > max_len or any(char in text for char in "\x00\r\n"):
        raise PayloadError(f"{field} is missing or invalid.")
    return text


def normalize_timestamp(value: object, *, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise PayloadError(f"{field} must be an ISO-8601 timestamp.")
    text = value.strip()
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError as exc:
        raise PayloadError(f"{field} must be an ISO-8601 timestamp.") from exc
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=UTC)
    return parsed.astimezone(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def _repository(payload: dict) -> str | None:
    repository = payload.get("repository")
    if repository is None:
        return None
    if not isinstance(repository, dict):
        raise PayloadError("repository must be an object.")
    full_name = repository.get("full_name")
    if full_name is None:
        return None
    return _text(full_name, field="repository.full_name", max_len=200)


def _parse_push(payload: dict) -> ParsedEvent:
    ref = _text(payload.get("ref"), field="ref", max_len=300)
    if ref.startswith("refs/tags/"):
        raise IgnoredEvent("tag_push")
    prefix = "refs/heads/"
    if not ref.startswith(prefix):
        raise IgnoredEvent("unsupported_ref")
    branch = ref[len(prefix) :]
    branch = _text(branch, field="ref", max_len=250)
    if "head_commit" not in payload:
        raise PayloadError("head_commit is required.")
    head = payload.get("head_commit")
    if head is None:
        raise IgnoredEvent("branch_delete")
    if not isinstance(head, dict):
        raise PayloadError("head_commit must be an object.")
    commit_id = _text(head.get("id"), field="head_commit.id", max_len=64)
    if _COMMIT_ID.fullmatch(commit_id) is None:
        raise PayloadError("head_commit.id is missing or invalid.")
    timestamp = normalize_timestamp(head.get("timestamp"), field="head_commit.timestamp")
    pusher = payload.get("pusher")
    if not isinstance(pusher, dict):
        raise PayloadError("pusher must be an object.")
    author = _text(pusher.get("name"), field="pusher.name", max_len=100)
    return ParsedEvent(
        author=author,
        action="push",
        to_branch=branch,
        from_branch=None,
        timestamp=timestamp,
        request_id=commit_id,
        repository=_repository(payload),
    )


def _parse_pull_request(payload: dict) -> ParsedEvent:
    action = _text(payload.get("action"), field="action", max_len=40)
    pull = payload.get("pull_request")
    if not isinstance(pull, dict):
        raise PayloadError("pull_request must be an object.")
    author_obj = pull.get("user")
    if not isinstance(author_obj, dict):
        raise PayloadError("pull_request.user must be an object.")
    author = _text(author_obj.get("login"), field="pull_request.user.login", max_len=100)
    head = pull.get("head")
    base = pull.get("base")
    if not isinstance(head, dict) or not isinstance(base, dict):
        raise PayloadError("pull_request head and base must be objects.")
    from_branch = _text(head.get("ref"), field="pull_request.head.ref", max_len=250)
    to_branch = _text(base.get("ref"), field="pull_request.base.ref", max_len=250)
    request_id = _pull_request_id(pull.get("id"))
    repository = _repository(payload)

    if action in _STORED_PULL_ACTIONS:
        stamp_field = "updated_at" if action == "reopened" else "created_at"
        raw_stamp = pull.get(stamp_field) or pull.get("created_at")
        timestamp = normalize_timestamp(raw_stamp, field=f"pull_request.{stamp_field}")
        return ParsedEvent(
            author=author,
            action="pull_request",
            to_branch=to_branch,
            from_branch=from_branch,
            timestamp=timestamp,
            request_id=request_id,
            repository=repository,
        )

    if action == "closed":
        merged = pull.get("merged")
        if merged is False or merged is None:
            raise IgnoredEvent("pull_request_closed_unmerged")
        if merged is not True:
            raise PayloadError("pull_request.merged must be a boolean.")
        timestamp = normalize_timestamp(pull.get("merged_at"), field="pull_request.merged_at")
        return ParsedEvent(
            author=author,
            action="merge",
            to_branch=to_branch,
            from_branch=from_branch,
            timestamp=timestamp,
            request_id=request_id,
            repository=repository,
        )

    raise IgnoredEvent("pull_request_action_not_stored")


def _pull_request_id(value: object) -> str:
    if isinstance(value, bool) or not isinstance(value, int) or value < 1:
        raise PayloadError("pull_request.id must be a positive integer.")
    return str(value)
