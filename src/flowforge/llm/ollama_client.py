from __future__ import annotations

import json
import re
from typing import Any, TypeVar

import requests
from pydantic import BaseModel, ValidationError

from flowforge.llm.structured_generation import build_structured_prompt
from flowforge.utils.errors import FlowForgeError


ModelT = TypeVar("ModelT", bound=BaseModel)


class OllamaStructuredClient:
    """Small wrapper around the Ollama generate API for structured outputs."""

    def __init__(self, *, base_url: str, model: str, timeout_seconds: int = 90) -> None:
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout_seconds = timeout_seconds

    def generate_structured(
        self,
        *,
        prompt: str,
        schema: type[ModelT],
        metadata: dict[str, object] | None = None,
        system_prompt: str = "You are a precise software engineering workflow assistant.",
    ) -> ModelT:
        """Generate a JSON object and validate it against a Pydantic schema."""
        full_prompt = build_structured_prompt(system_prompt=system_prompt, user_prompt=prompt, schema=schema)
        payload = {
            "model": self.model,
            "prompt": full_prompt,
            "stream": False,
            "format": "json",
            "options": {"temperature": 0.1, "num_predict": 700},
        }
        raw = "{}"
        try:
            response = requests.post(
                f"{self.base_url}/api/generate",
                json=payload,
                timeout=self.timeout_seconds,
            )
            response.raise_for_status()
            raw = str(response.json().get("response", "{}"))
            parsed = json.loads(self._extract_json_object(raw))
            return schema.model_validate(parsed)
        except (requests.RequestException, json.JSONDecodeError, ValidationError) as exc:
            meta = f" metadata={metadata}" if metadata else ""
            raw_preview = raw.replace("\n", "\\n")[:180]
            raise FlowForgeError(
                f"Ollama structured generation failed.{meta} "
                f"error_type={type(exc).__name__} raw_preview={raw_preview!r}"
            ) from exc

    @staticmethod
    def _extract_json_object(raw: str) -> str:
        """Extract the JSON object from a model response that may include fencing."""
        stripped = raw.strip()
        fenced = re.match(r"^```(?:json)?\s*(.*?)\s*```$", stripped, re.DOTALL)
        if fenced is not None:
            return fenced.group(1)
        return stripped
