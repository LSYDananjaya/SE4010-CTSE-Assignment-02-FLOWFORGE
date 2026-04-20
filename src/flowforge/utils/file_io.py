from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def ensure_directory(path: Path) -> Path:
    """Create a directory if needed and return it."""
    path.mkdir(parents=True, exist_ok=True)
    return path


def read_json(path: Path) -> dict[str, Any]:
    """Read a JSON file into a dictionary."""
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: dict[str, Any]) -> None:
    """Write a dictionary to a JSON file."""
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
