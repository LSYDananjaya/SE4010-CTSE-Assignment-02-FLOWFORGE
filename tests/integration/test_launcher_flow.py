from __future__ import annotations

from pathlib import Path
from time import sleep

from flowforge.launcher.app import LauncherApp
from flowforge.launcher.models import SessionMode, SessionState
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
    assert app.state.workspace_markers
    assert any(entry.text == "Workspace ready." for entry in app.state.transcript)
    assert not any("Workspace set to" in entry.text for entry in app.state.transcript)
    assert not any("Enter a workspace path." in entry.text for entry in app.state.transcript)
    assert app.state.current_run is not None
    assert app.state.current_run.run_id == runs[0]["run_id"]


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
    assert any("Failure Cause: Task T2 references unknown dependencies: ['T9']" in text for text in transcript_texts)
    assert any(agent.status == "failed" for agent in app.state.agent_progress if agent.name == "Planning Agent")
    assert not any("Agent started" in text or "Agent completed" in text for text in transcript_texts)
    assert len(tui.states) >= 3
    assert app.state.current_run is not None
    assert app.state.current_run.failure_cause == "Task T2 references unknown dependencies: ['T9']"


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
    assert any("Running workflow for" in text for text in transcript_texts)
    assert any(
        agent.status == "running"
        for state in tui.states
        for agent in state.agent_progress
        if agent.name == "Intake Agent"
    )
    assert not any("Agent started" in text or "Agent completed" in text for text in transcript_texts)
    assert len(tui.states) <= 6


def test_session_flow_keeps_agent_progress_rail_visible(sample_repo: Path, tmp_path: Path) -> None:
    persistence = PersistenceService(base_dir=tmp_path / "data")
    reporting = ReportingService(base_dir=tmp_path / "data")
    trace_writer = JsonTraceWriter(base_dir=tmp_path / "data")
    prompt_io = FakePromptIO(
        [
            f"/project {sample_repo}",
            "review @src/auth_service.py",
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

    assert any(state.agent_progress for state in tui.states)
    assert any(
        agent.status == "completed"
        for state in tui.states
        for agent in state.agent_progress
        if agent.name == "Context Agent"
    )
    assert any(
        agent.status == "failed"
        for state in tui.states
        for agent in state.agent_progress
        if agent.name == "Planning Agent"
    )
    assert any(
        any(agent.status == "completed" for agent in state.agent_progress)
        for state in tui.states
    )


def test_session_flow_enters_project_selection_when_project_command_submits_without_argument(tmp_path: Path) -> None:
    persistence = PersistenceService(base_dir=tmp_path / "data")
    reporting = ReportingService(base_dir=tmp_path / "data")
    trace_writer = JsonTraceWriter(base_dir=tmp_path / "data")
    prompt_io = FakePromptIO(["/project", "/exit"])
    tui = RecordingTui()
    app = LauncherApp(
        persistence=persistence,
        reporting=reporting,
        trace_writer=trace_writer,
        workflow=StubWorkflow(),
        prompt_io=prompt_io,
        sample_dir=Path("sample_inputs"),
        tui=tui,
    )

    app.run()

    assert prompt_io.placeholders[0] == "Describe a bug or feature request..."
    assert prompt_io.placeholders[1] == "Enter a workspace path..."
    assert any(
        state.mode == SessionMode.PROJECT_SELECTION
        for state in tui.states
    )
    assert any(
        entry.text == "Enter a workspace path."
        for state in tui.states
        for entry in state.transcript
    )


def test_session_flow_runs_with_finalized_attached_file(sample_repo: Path, tmp_path: Path) -> None:
    persistence = PersistenceService(base_dir=tmp_path / "data")
    reporting = ReportingService(base_dir=tmp_path / "data")
    trace_writer = JsonTraceWriter(base_dir=tmp_path / "data")
    prompt_io = FakePromptIO(
        [
            f"/project {sample_repo}",
            "what improvements can be done on @src/auth_service.py ",
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
    assert app.state.attachments == ["src/auth_service.py"]


def test_session_flow_collapses_previous_run_when_new_workflow_starts(sample_repo: Path, tmp_path: Path) -> None:
    persistence = PersistenceService(base_dir=tmp_path / "data")
    reporting = ReportingService(base_dir=tmp_path / "data")
    trace_writer = JsonTraceWriter(base_dir=tmp_path / "data")
    prompt_io = FakePromptIO(
        [
            f"/project {sample_repo}",
            "review @src/auth_service.py",
            "fix timeout in @src/auth_service.py",
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

    assert app.state.current_run is not None
    assert app.state.current_run.title.startswith("fix timeout")
    assert app.state.run_history
    assert app.state.run_history[0].title.startswith("review")
    assert len([entry for entry in app.state.transcript if entry.text.startswith("Run run-")]) == 1
