from __future__ import annotations

import os

import pytest

from flowforge.graph.workflow import FlowForgeWorkflow
from flowforge.llm.ollama_client import OllamaStructuredClient
from flowforge.models.requests import UserRequest


@pytest.mark.skipif(os.getenv("FLOWFORGE_LIVE_OLLAMA") != "1", reason="Live Ollama smoke test is opt-in.")
def test_end_to_end_live_ollama(sample_repo) -> None:
    workflow = FlowForgeWorkflow.from_live_llm(
        OllamaStructuredClient(base_url="http://localhost:11434", model="qwen2.5:3b")
    )
    result = workflow.run(
        UserRequest(
            title="Login timeout bug",
            description="Fix login timeout.",
            request_type="bug",
            constraints=["Local only"],
            reporter="qa",
            repo_path=str(sample_repo),
        )
    )

    assert result.qa_result is not None
