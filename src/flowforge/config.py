from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel, Field


class AppConfig(BaseModel):
    """Application-level configuration values."""

    base_dir: Path
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "qwen2.5:3b"
    ollama_timeout_seconds: int = 90
    repo_max_files: int = 5
    repo_snippet_chars: int = 600

    @classmethod
    def from_base_dir(cls, base_dir: Path) -> "AppConfig":
        """Create config and ensure the base output directory exists."""
        base_dir.mkdir(parents=True, exist_ok=True)
        (base_dir / "reports").mkdir(parents=True, exist_ok=True)
        (base_dir / "traces").mkdir(parents=True, exist_ok=True)
        return cls(base_dir=base_dir)
