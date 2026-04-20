from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from flowforge.config import AppConfig
from flowforge.services.tracing import JsonTraceWriter
import main as main_module


def test_main_entrypoint_help_runs_from_project_root() -> None:
    project_root = Path(__file__).resolve().parents[2]
    result = subprocess.run(
        [sys.executable, "main.py", "--help"],
        cwd=project_root,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0
    assert "Run the FlowForge local multi-agent workflow." in result.stdout


def test_build_workflow_returns_shared_trace_writer(monkeypatch, tmp_path: Path) -> None:
    captured: dict[str, object] = {}

    class FakeWorkflow:
        def __init__(self, trace_writer: JsonTraceWriter) -> None:
            self.trace_writer = trace_writer

    def fake_from_live_llm(*, llm_client: object, trace_writer: JsonTraceWriter | None = None) -> FakeWorkflow:
        assert trace_writer is not None
        captured["llm_client"] = llm_client
        captured["trace_writer"] = trace_writer
        return FakeWorkflow(trace_writer=trace_writer)

    monkeypatch.setattr(main_module.FlowForgeWorkflow, "from_live_llm", fake_from_live_llm)
    config = AppConfig.from_base_dir(tmp_path / "data")

    workflow, persistence, reporting, trace_writer = main_module.build_workflow(config, use_live_ollama=True)

    assert persistence.base_dir == config.base_dir
    assert reporting.base_dir == config.base_dir
    assert workflow.trace_writer is trace_writer
    assert captured["trace_writer"] is trace_writer
