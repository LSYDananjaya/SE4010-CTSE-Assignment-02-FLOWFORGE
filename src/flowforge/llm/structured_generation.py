from __future__ import annotations

import json
from typing import TypeVar

from pydantic import BaseModel


ModelT = TypeVar("ModelT", bound=BaseModel)


def build_structured_prompt(*, system_prompt: str, user_prompt: str, schema: type[ModelT]) -> str:
    """Compose a compact structured-generation prompt for Ollama."""
    schema_json = json.dumps(schema.model_json_schema(), indent=2)
    return (
        f"{system_prompt.strip()}\n\n"
        "Return valid JSON only.\n"
        f"JSON schema:\n{schema_json}\n\n"
        f"Task:\n{user_prompt.strip()}"
    )
