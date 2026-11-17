"""Structured API errors. Responses never include exception text or secrets."""

from __future__ import annotations

from flask import jsonify


def error_response(code: str, message: str, status: int):
    return jsonify({"error": {"code": code, "message": message}}), status
