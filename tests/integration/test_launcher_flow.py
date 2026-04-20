from __future__ import annotations

from pathlib import Path
from time import sleep

from flowforge.launcher.app import LauncherApp
from flowforge.launcher.models import SessionState
from flowforge.models.requests import UserRequest
from flowforge.models.state import WorkflowState
from flowforge.services.persistence import PersistenceService
from flowforge.services.reporting import ReportingService
from flowforge.services.tracing import JsonTraceWriter


class FakePromptIO:
    """Deterministic prompt backend for session integration tests."""

    def __init__(self, responses: list[str]) -> None:
        self._responses = responses
        self.placeholders: list[str] = []

    def read_input(
        self,
        *,
        placeholder: str,
        workspace_root: Path | None = None,
        current_text: str = "",
        recent_projects: list[object] | None = None,
    ) -> str:
        self.placeholders.append(placeholder)
        return self._responses.pop(0)


class StubWorkflow:
    """Minimal workflow stub returning a completed state."""

    def run(self, request: UserRequest) -> WorkflowState:
        state = WorkflowState.initial(request=request)
        state.workflow_status = "completed"
        state.trace_file = "trace.jsonl"
        return state


class ProgressWorkflow:
    """Workflow stub that emits trace events and fails during planning."""

    def __init__(self, trace_writer: JsonTraceWriter) -> None:
        self.trace_writer = trace_writer

    def run(self, request: UserRequest) -> WorkflowState:
        state = WorkflowState.initial(request=request)
        for node_name in ("intake", "context"):
            self.trace_writer.write_event(
                run_id=state.run_id,
                node_name=node_name,
                status="started",
                latency_ms=0.0,
                detail="",
            )
            sleep(0.01)
            self.trace_writer.write_event(
                run_id=state.run_id,
                node_name=node_name,
                status="success",
                latency_ms=12.0,
                detail="",
            )
        self.trace_writer.write_event(
            run_id=state.run_id,
            node_name="planning",
            status="started",
            latency_ms=0.0,
            detail="",
        )
        sleep(0.01)
        self.trace_writer.write_event(
            run_id=state.run_id,
            node_name="planning",
            status="error",
            latency_ms=24.0,
            detail="Task T2 references unknown dependencies: ['T9']",
        )
        state.workflow_status = "failed"
        state.trace_file = self.trace_writer.trace_path_for(state.run_id)
        state.errors = [
            "Task T2 references unknown dependencies: ['T9']",
            "Planning Agent failed.",
            "QA Agent requires intake, context, and planning outputs.",
        ]
        return state


class DelayedStartWorkflow:
    """Workflow stub that pauses before sending its first progress event."""

    def __init__(self, trace_writer: JsonTraceWriter) -> None:
        self.trace_writer = trace_writer

    def run(self, request: UserRequest) -> WorkflowState:
        state = WorkflowState.initial(request=request)
        sleep(0.05)
        self.trace_writer.write_event(
            run_id=state.run_id,
            node_name="intake",
            status="started",
            latency_ms=0.0,
            detail="",
        )
        sleep(0.01)
        self.trace_writer.write_event(
            run_id=state.run_id,
            node_name="intake",
            status="success",
            latency_ms=10.0,
            detail="",
        )
        state.workflow_status = "completed"
        state.trace_file = self.trace_writer.trace_path_for(state.run_id)
        return state


class RecordingTui:
    """Capture rendered session output during launcher tests."""

    def __init__(self) -> None:
        self.states: list[SessionState] = []

    def render_session(self, *, state: SessionState) -> None:
        self.states.append(state.model_copy(deep=True))


def test_session_flow_selects_project_and_runs(sample_repo: Path, tmp_path: Path) -> None:
    persistence = PersistenceService(base_dir=tmp_path / "data")
    reporting = ReportingService(base_dir=tmp_path / "data")
    trace_writer = JsonTraceWriter(base_dir=tmp_path / "data")
    prompt_io = FakePromptIO(
        [
            f"/project {sample_repo}",
            "fix the login timeout in @src/auth_service.py",
            "/exit",
        ]
    )
    app = LauncherApp(
        persistence=persistence,
        reporting=reporting,
        trace_writer=trace_writer,
        workflow=StubWorkflow(),
        prompt_io=prompt_io,
        sample_dir=Path("sample_inputs"),
    )

    app.run()

    runs = persistence.fetch_runs()
    assert len(runs) == 1
    assert runs[0]["workflow_status"] == "completed"
    assert persistence.fetch_recent_projects()[0]["path"] == str(sample_repo)


def test_session_flow_shows_live_agent_progress_and_root_cause(sample_repo: Path, tmp_path: Path) -> None:
    persistence = PersistenceService(base_dir=tmp_path / "data")
    reporting = ReportingService(base_dir=tmp_path / "data")
    trace_writer = JsonTraceWriter(base_dir=tmp_path / "data")
    prompt_io = FakePromptIO(
        [
            f"/project {sample_repo}",
            "what improvements can be done on @src/auth_service.py",
            "/exit",
        ]
    )
    tui = RecordingTui()
    app = LauncherApp(
        persistence=persistence,
        reporting=reporting,
        trace_writer=trace_writer,
        workflow=ProgressWorkflow(trace_writer),
        prompt_io=prompt_io,
        sample_dir=Path("sample_inputs"),
        tui=tui,
    )

    app.run()

    transcript_texts = [entry.text for entry in app.state.transcript]
    assert "No workspace selected. Use /project to choose one." not in transcript_texts
    assert any("Intake Agent started" in text for text in transcript_texts)
    assert any("Context Agent completed" in text for text in transcript_texts)
    assert any("Planning Agent failed: Task T2 references unknown dependencies: ['T9']" in text for text in transcript_texts)
    assert any("Failure Cause: Task T2 references unknown dependencies: ['T9']" in text for text in transcript_texts)
    assert len(tui.states) >= 3


def test_session_flow_shows_waiting_state_without_excess_idle_rerenders(sample_repo: Path, tmp_path: Path) -> None:
    persistence = PersistenceService(base_dir=tmp_path / "data")
    reporting = ReportingService(base_dir=tmp_path / "data")
    trace_writer = JsonTraceWriter(base_dir=tmp_path / "data")
    prompt_io = FakePromptIO(
        [
            f"/project {sample_repo}",
            "what improvements can be done on @src/auth_service.py",
            "/exit",
        ]
    )
    tui = RecordingTui()
    app = LauncherApp(
        persistence=persistence,
        reporting=reporting,
        trace_writer=trace_writer,
        workflow=DelayedStartWorkflow(trace_writer),
        prompt_io=prompt_io,
        sample_dir=Path("sample_inputs"),
        tui=tui,
    )

    app.run()

    transcript_texts = [entry.text for entry in app.state.transcript]
    assert any(
        "Waiting for Intake Agent..." in entry.text
        for state in tui.states
        for entry in state.transcript
    )
    assert any("Intake Agent started" in text for text in transcript_texts)
    assert any("Intake Agent completed" in text for text in transcript_texts)
    assert len(tui.states) <= 6
