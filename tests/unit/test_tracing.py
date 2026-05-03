from __future__ import annotations

import json
from pathlib import Path

from flowforge.services.tracing import JsonTraceWriter


def test_trace_writer_persists_agentops_metadata(tmp_path: Path) -> None:
    writer = JsonTraceWriter(base_dir=tmp_path)

    writer.write_event(
        run_id="run-123",
        node_name="context",
        status="success",
        latency_ms=12.34,
        detail="",
        agent_input_summary="Feature request for CategoryPicker accessibility improvements.",
        tool_name="RepoContextFinderTool",
        tool_input_summary="repo_path=sample_repo, attachments=['src/components/CategoryPicker.tsx']",
        tool_output_summary="2 repository candidates scored and 1 snippet selected.",
        fallback_used=False,
        llm_output_summary="Selected the attached component and one related test file.",
        failure_cause="",
    )

    payload = json.loads((tmp_path / "traces" / "run-123.jsonl").read_text(encoding="utf-8").splitlines()[0])

    assert payload["agent_input_summary"].startswith("Feature request")
    assert payload["tool_name"] == "RepoContextFinderTool"
    assert payload["tool_input_summary"].startswith("repo_path=")
    assert payload["tool_output_summary"].endswith("selected.")
    assert payload["fallback_used"] is False
    assert payload["llm_output_summary"].startswith("Selected the attached")
    assert payload["failure_cause"] == ""
