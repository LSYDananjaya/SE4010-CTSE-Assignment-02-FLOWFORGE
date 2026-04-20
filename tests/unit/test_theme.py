from __future__ import annotations

from rich.console import Console, Group
from rich.layout import Layout

from flowforge.launcher.models import TraceSummaryRow
from flowforge.tui.renderer import ClaudeLikeRenderer
from flowforge.tui.theme import build_console, render_banner, render_status_panel, render_welcome_panel


def test_build_console_uses_custom_theme() -> None:
    console = build_console(record=True)

    assert isinstance(console, Console)
    assert console.get_style("focus").color is not None
    assert console.get_style("active").color is not None
    assert console.get_style("muted").color is not None
    assert console.get_style("danger").color is not None


def test_render_banner_contains_branding() -> None:
    console = build_console(record=True)
    console.print(render_banner())
    output = console.export_text()

    assert "qwen2.5:3b" in output
    assert "/help" in output
    assert "Tips" in output


def test_render_banner_shows_workspace_when_set() -> None:
    console = build_console(record=True)
    console.print(render_banner(workspace="C:\\my\\project"))
    output = console.export_text()

    assert "C:\\my\\project" in output


def test_render_status_panel_includes_expected_labels() -> None:
    console = build_console(record=True)
    console.print(render_status_panel(title="Planning", status="running", body="Generating tasks"))
    output = console.export_text()

    assert "Planning" in output
    assert "RUNNING" in output


def test_renderer_builds_layout_regions() -> None:
    renderer = ClaudeLikeRenderer()

    layout = renderer.compose_screen(
        mode="Launcher",
        main=renderer.render_compact_menu(
            title="Actions",
            items=[("new_run", "Start new run"), ("recent_runs", "View recent runs")],
        ),
        context=renderer.render_context_list(
            title="Context",
            rows=[("Project", "Not selected"), ("Runtime", "qwen2.5:3b")],
        ),
        status_text="Ready",
    )

    assert isinstance(layout, Layout)
    assert layout["header"] is not None
    assert layout["body"] is not None
    assert layout["status"] is not None
    assert layout["body"]["main"] is not None
    assert layout["body"]["context"] is not None


def test_renderer_execution_layout_includes_agent_rail() -> None:
    renderer = ClaudeLikeRenderer()

    rail = renderer.render_agent_rail(
        [
            ("Intake", "completed"),
            ("Context", "running"),
            ("Planning", "pending"),
            ("QA", "pending"),
        ]
    )
    layout = renderer.compose_screen(
        mode="Running",
        main=renderer.render_context_list(
            title="Activity",
            rows=[("Current", "Context agent retrieving snippets"), ("Files", "2 selected")],
        ),
        context=rail,
        status_text="Context agent running",
    )

    console = build_console(record=True)
    console.print(layout)
    output = console.export_text()

    assert "Intake" in output
    assert "Context" in output
    assert "Planning" in output
    assert "QA" in output
    assert "Context agent running" in output


def test_renderer_recent_runs_view_is_compact() -> None:
    renderer = ClaudeLikeRenderer()
    layout = renderer.compose_screen(
        mode="Recent Runs",
        main=renderer.render_runs_table(
            runs=[
                {
                    "run_id": "run-1",
                    "request_title": "Login timeout bug",
                    "workflow_status": "completed",
                    "qa_approved": 1,
                }
            ]
        ),
        context=renderer.render_trace_preview(
            [TraceSummaryRow(node_name="qa", status="success", latency_ms=12.0)]
        ),
        status_text="Showing recent runs",
    )

    console = build_console(record=True)
    console.print(layout)
    output = console.export_text()

    assert "Recent Runs" in output
    assert "Login timeout bug" in output
    assert "qa" in output
