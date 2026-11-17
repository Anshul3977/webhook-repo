"""Display formatting for stored events."""

from __future__ import annotations

from datetime import datetime


def format_timestamp(iso_timestamp: str) -> str:
    """Format a normalized UTC timestamp as '1st April 2021 - 9:30 PM UTC'."""
    text = iso_timestamp.strip()
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    parsed = datetime.fromisoformat(text)
    day = parsed.day
    if 4 <= day <= 20 or 24 <= day <= 30:
        suffix = "th"
    else:
        suffix = ("st", "nd", "rd")[day % 10 - 1]
    hour = parsed.strftime("%I").lstrip("0")
    rest = parsed.strftime("%M %p")
    month = parsed.strftime("%B")
    return f"{day}{suffix} {month} {parsed.year} - {hour}:{rest} UTC"


def format_message(event: dict) -> str:
    when = format_timestamp(event["timestamp"])
    author = event["author"]
    action = event["action"]
    if action == "push":
        return f"{author} pushed to {event['to_branch']} on {when}"
    if action == "pull_request":
        return (
            f"{author} submitted a pull request from {event['from_branch']} "
            f"to {event['to_branch']} on {when}"
        )
    if action == "merge":
        return f"{author} merged branch {event['from_branch']} to {event['to_branch']} on {when}"
    raise ValueError(f"unknown action: {action}")
