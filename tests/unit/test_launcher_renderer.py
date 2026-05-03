from __future__ import annotations

from flowforge.launcher.models import SessionEntry, SessionEntryKind, SessionRunDetail, SessionRunHistoryEntry, TraceSummaryRow
from flowforge.tui.renderer import ClaudeLikeRenderer
from flowforge.tui.theme import build_console


def test_initial_session_screen_contains_transcript() -> None:
    renderer = ClaudeLikeRenderer()
    console = build_console(record=True)
    layout = renderer.compose_session_screen(
        transcript_entries=[
            SessionEntry(kind=SessionEntryKind.SYSTEM, text="No workspace selected. Use /project to choose one."),
        ],
        context_rows=[("Workspace", "None"), ("Attachments", "0 files")],
    )
    console.print(layout)
    output = console.export_text()

    assert "No workspace selected." in output
    assert "/project" in output
    assert "Workspace Selected" not in output


def test_session_screen_shows_workspace_when_set() -> None:
    renderer = ClaudeLikeRenderer()
    console = build_console(record=True)
    layout = renderer.compose_session_screen(
        transcript_entries=[SessionEntry(kind=SessionEntryKind.SYSTEM, text="Workspace ready.")],
        context_rows=[("Workspace", "sample_repo"), ("Mode", "Idle")],
        workspace_path=r"C:\repos\sample_repo",
        workspace_markers=["src", "package.json", "README.md"],
    )
    console.print(layout)
    output = console.export_text()

    assert "Workspace Selected" in output
    assert "sample_repo" in output
    assert "Workspace ready." in output
    assert "[ src ]" in output
    assert "Enter a workspace path." not in output


def test_session_screen_truncates_long_workspace_path() -> None:
    renderer = ClaudeLikeRenderer()
    console = build_console(record=True, )
    long_path = (
        r"C:\Users\USER\Documents\SE Projects\RP\Final Implementation"
        r"\FindAssure---Lost-Found-System---Research-Project\FindAssure"
    )
    layout = renderer.compose_session_screen(
        transcript_entries=[SessionEntry(kind=SessionEntryKind.SYSTEM, text="Workspace ready.")],
        context_rows=[("Workspace", "FindAssure"), ("Mode", "Idle")],
        workspace_path=long_path,
        workspace_markers=["src", "package.json", "README.md"],
    )
    console.print(layout)
    output = console.export_text()

    assert "..." in output
    assert "FindAssure" in output


def test_session_screen_stays_compact_for_short_transcript() -> None:
    renderer = ClaudeLikeRenderer()
    console = build_console(record=True)
    screen = renderer.compose_session_screen(
        transcript_entries=[
            SessionEntry(kind=SessionEntryKind.SYSTEM, text="No workspace selected."),
        ],
        context_rows=[("Workspace", "None"), ("Mode", "Idle")],
    )
    console.print(screen)
    output = console.export_text()

    assert len(output.splitlines()) < 18


def test_transcript_renders_different_entry_kinds() -> None:
    renderer = ClaudeLikeRenderer()
    console = build_console(record=True)
    entries = [
        SessionEntry(kind=SessionEntryKind.SYSTEM, text="System message"),
        SessionEntry(kind=SessionEntryKind.USER, text="User input"),
        SessionEntry(kind=SessionEntryKind.STATUS, text="Processing..."),
        SessionEntry(kind=SessionEntryKind.RESULT, text="Done!"),
        SessionEntry(kind=SessionEntryKind.ERROR, text="Something failed"),
    ]
    transcript = renderer.render_transcript(entries)
    console.print(transcript)
    output = console.export_text()

    assert "System message" in output
    assert "User input" in output
    assert "Processing..." in output
    assert "Done!" in output
    assert "Something failed" in output


def test_result_summary_renders_rows() -> None:
    renderer = ClaudeLikeRenderer()
    console = build_console(record=True)
    summary = renderer.render_result_summary(
        rows=[("Run", "abc-123"), ("Status", "completed")],
        title="Run Summary",
    )
    console.print(summary)
    output = console.export_text()

    assert "Run Summary" in output
    assert "abc-123" in output
    assert "completed" in output


def test_session_screen_renders_agent_progress_block() -> None:
    from flowforge.launcher.models import AgentProgressEntry

    renderer = ClaudeLikeRenderer()
    console = build_console(record=True)
    layout = renderer.compose_session_screen(
        transcript_entries=[SessionEntry(kind=SessionEntryKind.STATUS, text="Intake Agent started...")],
        context_rows=[("Workspace", "sample_repo"), ("Mode", "Running")],
        agent_progress=[
            AgentProgressEntry(name="Intake Agent", status="running", detail="Parsing request"),
            AgentProgressEntry(name="Context Agent", status="pending"),
            AgentProgressEntry(name="Planning Agent", status="pending"),
            AgentProgressEntry(name="QA Agent", status="pending"),
        ],
        workflow_active=True,
    )
    console.print(layout)
    output = console.export_text()

    assert "Agent Progress" in output
    assert "Intake Agent" in output
    assert "RUNNING" in output
    assert "Execution Summary" in output


def test_agent_progress_layout_separates_status_from_detail() -> None:
    from flowforge.launcher.models import AgentProgressEntry

    renderer = ClaudeLikeRenderer()
    console = build_console(record=True)
    panel = renderer.render_live_agent_progress(
        [
            AgentProgressEntry(name="Intake Agent", status="completed", detail="Completed in 6558ms"),
            AgentProgressEntry(name="Context Agent", status="running", detail="Processing request"),
        ]
    )
    console.print(panel)
    output = console.export_text()

    assert "Completed in 6558ms" in output
    assert "COMPLETEDCompleted" not in output


def test_agent_progress_renders_blocked_agents_as_secondary() -> None:
    from flowforge.launcher.models import AgentProgressEntry

    renderer = ClaudeLikeRenderer()
    console = build_console(record=True)
    panel = renderer.render_live_agent_progress(
        [
            AgentProgressEntry(name="Intake Agent", status="failed", detail="Structured output validation failed"),
            AgentProgressEntry(name="Context Agent", status="blocked", detail="Context Agent requires intake output."),
        ]
    )
    console.print(panel)
    output = console.export_text()

    assert "BLOCKED" in output
    assert "requires intake" in output


def test_session_screen_renders_latest_run_and_history() -> None:
    renderer = ClaudeLikeRenderer()
    console = build_console(record=True)
    layout = renderer.compose_session_screen(
        transcript_entries=[SessionEntry(kind=SessionEntryKind.STATUS, text="Running workflow for 'review card'...")],
        context_rows=[("Workspace", "sample_repo"), ("Mode", "Idle")],
        current_run=SessionRunDetail(
            run_id="run-1",
            title="review card",
            status="completed",
            trace_rows=[TraceSummaryRow(node_name="intake", status="success", latency_ms=1200)],
        ),
        run_history=[SessionRunHistoryEntry(run_id="run-0", title="old run", status="failed", summary="Previous failed run")],
    )
    console.print(layout)
    output = console.export_text()

    assert "Latest Run" in output
    assert "Previous Runs" in output
    assert "review card" in output
    assert "Previous failed run" in output


def test_latest_run_renders_failure_details_without_empty_sections() -> None:
    renderer = ClaudeLikeRenderer()
    console = build_console(record=True)
    run = SessionRunDetail(
        run_id="run-err",
        title="feature review",
        status="failed",
        failure_cause="Ollama structured generation failed: severity='unknown'",
        trace_rows=[TraceSummaryRow(node_name="intake", status="error", latency_ms=1000)],
    )

    console.print(renderer.render_latest_run(run))
    output = console.export_text()

    assert "Failure Details" in output
    assert "severity='unknown'" in output
    assert "Intake" not in output
