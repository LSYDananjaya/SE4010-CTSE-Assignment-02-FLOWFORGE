from __future__ import annotations

from rich.panel import Panel
from rich.table import Table

from flowforge.launcher.models import SessionState
from flowforge.models.outputs import ArtifactPaths
from flowforge.models.state import WorkflowState
from flowforge.tui.renderer import ClaudeLikeRenderer
from flowforge.tui.theme import build_console, render_banner, render_status_panel


class FlowForgeTui:
    """Render a compact Rich-based view of the workflow result."""

    def __init__(self) -> None:
        self.console = build_console()
        self.renderer = ClaudeLikeRenderer()
        self._banner_shown = False

    def render_session(
        self,
        *,
        state: SessionState,
    ) -> None:
        """Render the session frame: banner + flowing transcript."""
        self.console.clear()

        # Show welcome banner with workspace info
        self.console.print(render_banner())

        # Context rows for the renderer
        context_rows = [
            ("Workspace", state.workspace_path or "None"),
            ("Attachments", f"{len(state.attachments)} files"),
            ("Mode", state.mode.value),
        ]

        layout = self.renderer.compose_session_screen(
            transcript_entries=state.transcript,
            context_rows=context_rows,
            agent_progress=state.agent_progress,
            workspace_path=state.workspace_path,
            workspace_markers=state.workspace_markers,
            current_run=state.current_run,
            run_history=state.run_history,
            workflow_active=state.workflow_active,
        )
        self.console.print(layout)

    def render(self, *, result: WorkflowState, artifacts: ArtifactPaths) -> None:
        """Render final status, tasks, and artifact paths."""
        summary_rows = [
            ("Run", result.run_id),
            ("Status", result.workflow_status),
            ("Request", result.request.title),
        ]
        if result.intake_result is not None:
            summary_rows.append(("Category", result.intake_result.category))
        if result.context_bundle is not None:
            summary_rows.append(("Snippets", str(len(result.context_bundle.selected_snippets))))
        if result.qa_result is not None:
            summary_rows.append(("QA", "approved" if result.qa_result.approved else "review needed"))

        # New clean result summary
        self.console.print(self.renderer.render_result_summary(rows=summary_rows))

        if result.plan_result:
            tasks = Table(box=None, expand=True, show_header=True, header_style="muted")
            tasks.add_column("Task", style="focus")
            tasks.add_column("Title", style="text")
            tasks.add_column("Priority", style="muted")
            for task in result.plan_result.tasks:
                tasks.add_row(task.task_id, task.title, task.priority)
            self.console.print(
                Panel.fit(
                    tasks,
                    title="[section]Plan[/section]",
                    border_style="border",
                )
            )

        # Artifacts
        self.console.print(self.renderer.render_artifacts(
            markdown_path=artifacts.markdown_report,
            json_path=artifacts.json_report,
            trace_path=artifacts.trace_file,
        ))

        self.console.print(
            render_status_panel(
                title=f"Run {result.run_id}",
                status=result.workflow_status,
                body=f"Request: {result.request.title}",
            )
        )

    def render_recent_runs(self, *, runs: list[dict[str, object]], trace_preview: list[object]) -> None:
        """Render recent runs and an optional trace preview."""
        layout = self.renderer.compose_screen(
            mode="Recent Runs",
            main=self.renderer.render_runs_table(runs=runs),
            context=self.renderer.render_trace_preview(list(trace_preview)),
            status_text="Reviewing recent FlowForge runs",
        )
        self.console.print(layout)
