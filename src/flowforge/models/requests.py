from __future__ import annotations

import json
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field


RequestType = Literal["bug", "feature"]


class UserRequest(BaseModel):
    """Structured user input for the workflow."""

    title: str = Field(min_length=3)
    description: str = Field(min_length=10)
    request_type: RequestType
    constraints: list[str] = Field(default_factory=list)
    reporter: str = Field(default="unknown")
    repo_path: str = Field(min_length=1)
    attachments: list[str] = Field(default_factory=list)

    @classmethod
    def from_json_file(cls, path: Path, repo_path: str) -> "UserRequest":
        """Load a request payload from disk and attach the repository path."""
        payload = json.loads(path.read_text(encoding="utf-8"))
        payload["repo_path"] = repo_path
        return cls.model_validate(payload)
