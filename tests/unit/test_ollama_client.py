from __future__ import annotations

from typing import Any

import pytest

from flowforge.llm.ollama_client import OllamaStructuredClient
from flowforge.models.outputs import ContextBundle
from flowforge.utils.errors import FlowForgeError


class _FakeResponse:
    def __init__(self, payload: dict[str, Any]) -> None:
        self._payload = payload

    def raise_for_status(self) -> None:
        return None

    def json(self) -> dict[str, Any]:
        return self._payload


def test_ollama_client_reports_raw_response_preview_on_invalid_json(monkeypatch) -> None:
    def fake_post(*args, **kwargs) -> _FakeResponse:  # type: ignore[no-untyped-def]
        return _FakeResponse({"response": "```json\nnot-valid-json\n```"})

    monkeypatch.setattr("flowforge.llm.ollama_client.requests.post", fake_post)
    client = OllamaStructuredClient(base_url="http://localhost:11434", model="qwen2.5:3b")

    with pytest.raises(FlowForgeError, match="raw_preview="):
        client.generate_structured(
            prompt="Select relevant snippets.",
            schema=ContextBundle,
            metadata={"agent": "context", "run_id": "run-1"},
        )
