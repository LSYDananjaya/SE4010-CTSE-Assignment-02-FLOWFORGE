from __future__ import annotations

from flowforge.launcher.models import SessionEntry, SessionEntryKind
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


def test_session_screen_shows_workspace_when_set() -> None:
    renderer = ClaudeLikeRenderer()
    console = build_console(record=True)
    layout = renderer.compose_session_screen(
        transcript_entries=[SessionEntry(kind=SessionEntryKind.SYSTEM, text="Workspace ready.")],
        context_rows=[("Workspace", "sample_repo"), ("Mode", "Idle")],
    )
    console.print(layout)
    output = console.export_text()

    assert "sample_repo" in output
    assert "Workspace ready." in output


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
