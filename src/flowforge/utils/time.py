from __future__ import annotations

from datetime import UTC, datetime


def utc_now_iso() -> str:
    """Return the current UTC time in ISO-8601 format."""
    return datetime.now(UTC).isoformat()


def make_run_id() -> str:
    """Generate a timestamp-based run identifier."""
    return datetime.now(UTC).strftime("run-%Y%m%d-%H%M%S-%f")
