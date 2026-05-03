from __future__ import annotations

from collections.abc import Iterable

from rich import box
from rich.console import Group, RenderableType
from rich.layout import Layout
from rich.panel import Panel
from rich.rule import Rule
from rich.table import Table
from rich.text import Text

from flowforge.launcher.models import (
    AgentProgressEntry,
    SessionEntry,
    SessionEntryKind,
    SessionRunDetail,
    SessionRunHistoryEntry,
    TraceSummaryRow,
)


# ── Transcript prefix mapping ──────────────────────────────────────────────────
_ENTRY_PREFIX: dict[SessionEntryKind, tuple[str, str, str]] = {
    #                                 icon   icon-style         text-style
    SessionEntryKind.SYSTEM:  ("●",  "entry.system",   "entry.system"),
    SessionEntryKind.USER:    ("❯",  "entry.user",     "text"),
    SessionEntryKind.STATUS:  ("⟳",  "entry.status",   "entry.status"),
    SessionEntryKind.ERROR:   ("✗",  "entry.error",    "entry.error"),
    SessionEntryKind.RESULT:  ("✓",  "entry.result",   "entry.result"),
}


class ClaudeLikeRenderer:
    """Compose a clean, single-column conversational layout inspired by Claude Code / Gemini CLI."""

    # ── session screen (primary view) ──────────────────────────────────────

    def compose_session_screen(
        self,
        *,
        transcript_entries: list[SessionEntry],
        context_rows: list[tuple[str, str]],
        agent_progress: list[AgentProgressEntry] | None = None,
        workspace_path: str | None = None,
        workspace_markers: list[str] | None = None,
        current_run: SessionRunDetail | None = None,
        run_history: list[SessionRunHistoryEntry] | None = None,
        workflow_active: bool = False,
    ) -> RenderableType:
        """Compose a minimal session frame: transcript entries flowing downward."""
        parts: list[RenderableType] = []

        if workspace_path:
            parts.append(self.render_workspace_summary(workspace_path, workspace_markers or []))
            parts.append(Text(""))

        if agent_progress and (workflow_active or current_run is not None):
            parts.append(self.render_live_agent_progress(agent_progress))
            parts.append(Text(""))

        if current_run is not None:
            parts.append(self.render_latest_run(current_run))
            parts.append(Text(""))

        if run_history:
            parts.append(self.render_run_history(run_history))
            parts.append(Text(""))

        # Transcript
        if transcript_entries:
            parts.append(self.render_transcript(transcript_entries))

        return Group(*parts)

    def render_workspace_summary(self, workspace_path: str, markers: list[str]) -> Panel:
        """Render the selected workspace as a compact persistent summary block."""
        normalized_path = workspace_path.replace("/", "\\")
        display_name = normalized_path.rstrip("\\").split("\\")[-1] or normalized_path
        truncated_path = self._truncate_middle(normalized_path, max_length=88)

        rows: list[RenderableType] = [
            Text("Workspace Selected", style="muted"),
            Text(display_name, style="focus"),
            Text(truncated_path, style="path"),
        ]
        if markers:
            marker_line = Text()
            marker_line.append("Markers  ", style="muted")
            for index, marker in enumerate(markers[:3]):
                if index > 0:
                    marker_line.append("  ", style="muted")
                marker_line.append(f"[ {marker} ]", style="badge")
            rows.append(marker_line)
        return Panel(
            Group(*rows),
            border_style="border",
            box=box.ROUNDED,
            padding=(0, 1),
        )

    def render_live_agent_progress(self, agents: list[AgentProgressEntry]) -> Panel:
        """Render a dedicated workflow progress block for the four agents."""
        table = Table.grid(expand=True, padding=(0, 2))
        table.add_column(width=26)
        table.add_column(width=14, justify="center")
        table.add_column(ratio=1)
        spinner_frames = {
            "pending": "○",
            "running": "◉",
            "completed": "✓",
            "failed": "✗",
        }
        for agent in agents:
            marker = spinner_frames.get(agent.status, "•")
            status_style = self._status_style(agent.status)
            detail = agent.detail or {
                "pending": "",
                "running": "In progress",
                "completed": "Done",
                "failed": "Needs review",
            }.get(agent.status, "")
            badge = Text(f" {agent.status.upper()} ", style=f"{status_style} on #111827")
            table.add_row(
                Text.assemble((f"{marker} ", status_style), (agent.name, "text")),
                badge,
                Text(detail, style="muted"),
            )
        return Panel(
            Group(Text("Execution Summary", style="muted"), table),
            title="[section]Agent Progress[/section]",
            border_style="border",
            box=box.ROUNDED,
            padding=(0, 1),
        )

    def render_run_history(self, runs: list[SessionRunHistoryEntry]) -> Panel:
        """Render compact summaries for previous runs."""
        table = Table.grid(expand=True, padding=(0, 2))
        table.add_column(width=18, style="muted")
        table.add_column(width=12)
        table.add_column(ratio=1)
        for run in runs[:4]:
            table.add_row(
                run.run_id[-12:],
                Text(run.status.upper(), style=self._status_style(run.status)),
                Text(self._truncate_middle(run.summary or run.title, max_length=72), style="muted"),
            )
        return Panel(
            table,
            title="[section]Previous Runs[/section]",
            border_style="border",
            box=box.ROUNDED,
            padding=(0, 1),
        )

    def render_latest_run(self, run: SessionRunDetail) -> RenderableType:
        """Render the newest run as structured stacked report cards."""
        sections: list[RenderableType] = [self.render_run_summary(run)]
        if run.intake_result is not None:
            sections.append(self.render_intake_section(run))
        elif run.failure_cause:
            sections.append(self.render_failure_details(run))
        if run.context_bundle is not None:
            sections.append(self.render_context_section(run))
        if run.plan_result is not None:
            sections.append(self.render_plan_section(run))
        if run.qa_result is not None:
            sections.append(self.render_qa_section(run))
        if run.trace_rows:
            sections.append(self.render_trace_section(run))
        if run.artifacts is not None:
            sections.append(self.render_reports_section(run))
        return Group(*sections)

    def render_run_summary(self, run: SessionRunDetail) -> Panel:
        """Render top-level summary for the latest run."""
        grid = Table.grid(expand=True, padding=(0, 2))
        grid.add_column(width=16, style="muted")
        grid.add_column(ratio=1)
        grid.add_row("Run", run.run_id)
        grid.add_row("Status", Text(run.status.upper(), style=self._status_style(run.status)))
        grid.add_row("Request", run.title)
        if run.qa_result is not None:
            grid.add_row("QA", "Approved" if run.qa_result.approved else "Needs review")
        if run.failure_cause:
            grid.add_row("Failure", self._truncate_middle(run.failure_cause, max_length=84))
        return Panel(
            grid,
            title="[section]Latest Run[/section]",
            border_style="border",
            box=box.ROUNDED,
            padding=(0, 1),
        )

    def render_failure_details(self, run: SessionRunDetail) -> Panel:
        """Render compact failure diagnostics when the run fails early."""
        lines = [
            Text("Primary Failure", style="danger"),
            Text(self._truncate_middle(run.failure_cause, max_length=96), style="muted"),
        ]
        if "fallback" in run.failure_cause.lower():
            lines.append(Text("Deterministic fallback attempted.", style="warning"))
        return Panel(
            Group(*lines),
            title="[section]Failure Details[/section]",
            border_style="danger",
            box=box.ROUNDED,
            padding=(0, 1),
        )

    def render_intake_section(self, run: SessionRunDetail) -> Panel:
        intake = run.intake_result
        assert intake is not None
        grid = Table.grid(expand=True, padding=(0, 2))
        grid.add_column(width=14, style="muted")
        grid.add_column(ratio=1)
        grid.add_row("Category", intake.category)
        grid.add_row("Severity", intake.severity)
        grid.add_row("Scope", intake.scope)
        grid.add_row("Summary", self._truncate_middle(intake.summary, max_length=84))
        if intake.goals:
            grid.add_row("Goals", ", ".join(intake.goals[:3]))
        return Panel(grid, title="[section]Intake[/section]", border_style="border", box=box.ROUNDED, padding=(0, 1))

    def render_context_section(self, run: SessionRunDetail) -> Panel:
        context = run.context_bundle
        assert context is not None
        lines: list[RenderableType] = [
            Text(f"{len(context.selected_snippets)} snippets from {context.files_considered} files", style="muted")
        ]
        for snippet in context.selected_snippets[:4]:
            lines.append(Text.assemble(("• ", "focus"), (snippet.path, "path")))
            lines.append(Text(self._truncate_middle(snippet.reason, max_length=88), style="muted"))
        return Panel(Group(*lines), title="[section]Context[/section]", border_style="border", box=box.ROUNDED, padding=(0, 1))

    def render_plan_section(self, run: SessionRunDetail) -> Panel:
        plan = run.plan_result
        assert plan is not None
        lines: list[RenderableType] = [Text(self._truncate_middle(plan.summary, max_length=88), style="muted")]
        table = Table.grid(expand=True, padding=(0, 2))
        table.add_column(width=6, style="focus")
        table.add_column(ratio=1)
        table.add_column(width=10, style="muted")
        for task in plan.tasks[:4]:
            table.add_row(task.task_id, self._truncate_middle(task.title, max_length=54), task.priority.upper())
        lines.append(table)
        if plan.overall_risks:
            lines.append(Text("Risks", style="warning"))
            for risk in plan.overall_risks[:2]:
                lines.append(Text(f"• {self._truncate_middle(risk, max_length=88)}", style="muted"))
        return Panel(Group(*lines), title="[section]Implementation Plan[/section]", border_style="border", box=box.ROUNDED, padding=(0, 1))

    def render_qa_section(self, run: SessionRunDetail) -> Panel:
        qa = run.qa_result
        assert qa is not None
        lines: list[RenderableType] = [
            Text("APPROVED" if qa.approved else "NEEDS REVIEW", style="success" if qa.approved else "warning"),
            Text(self._truncate_middle(qa.summary, max_length=88), style="muted"),
        ]
        if qa.rubric_checks:
            checks = Table.grid(expand=True, padding=(0, 2))
            checks.add_column(width=24, style="muted")
            checks.add_column(width=8)
            for check, passed in qa.rubric_checks.items():
                checks.add_row(check, Text("PASS" if passed else "MISS", style="success" if passed else "warning"))
            lines.append(checks)
        return Panel(Group(*lines), title="[section]QA[/section]", border_style="border", box=box.ROUNDED, padding=(0, 1))

    def render_trace_section(self, run: SessionRunDetail) -> Panel:
        table = Table(expand=True, box=None, show_header=True, header_style="muted")
        table.add_column("Agent", style="text")
        table.add_column("Status", width=12)
        table.add_column("Latency", justify="right", width=12)
        total_ms = 0.0
        for row in run.trace_rows:
            table.add_row(row.node_name, Text(row.status.upper(), style=self._status_style(row.status)), f"{row.latency_ms:.0f}ms")
            total_ms += row.latency_ms
        footer = Text(f"Total {total_ms:.0f}ms", style="muted")
        return Panel(Group(table, footer), title="[section]Trace[/section]", border_style="border", box=box.ROUNDED, padding=(0, 1))

    def render_reports_section(self, run: SessionRunDetail) -> Panel:
        assert run.artifacts is not None
        lines = [
            Text.assemble(("• ", "focus"), ("Markdown  ", "muted"), (self._truncate_middle(run.artifacts.markdown_report, max_length=80), "path")),
            Text.assemble(("• ", "focus"), ("JSON      ", "muted"), (self._truncate_middle(run.artifacts.json_report, max_length=80), "path")),
            Text.assemble(("• ", "focus"), ("Trace     ", "muted"), (self._truncate_middle(run.artifacts.trace_file, max_length=80), "path")),
        ]
        return Panel(Group(*lines), title="[section]Reports[/section]", border_style="border", box=box.ROUNDED, padding=(0, 1))

    # ── transcript ─────────────────────────────────────────────────────────

    def render_transcript(self, entries: list[SessionEntry]) -> RenderableType:
        """Render transcript as conversational lines with styled prefixes."""
        lines: list[RenderableType] = []
        if not entries:
            lines.append(Text.assemble(("  ● ", "entry.system"), ("FlowForge ready.", "entry.system")))
            return Group(*lines)

        _BOX_CHARS = ("╭", "╰", "│")

        for entry in entries[-80:]:
            icon, icon_style, text_style = _ENTRY_PREFIX.get(
                entry.kind, ("·", "muted", "text")
            )

            # Empty entries → blank line
            if not entry.text.strip():
                lines.append(Text(""))
                continue

            # Box-drawing lines (from /help) render without prefix
            if entry.kind == SessionEntryKind.SYSTEM and entry.text.lstrip().startswith(_BOX_CHARS):
                lines.append(Text.assemble(("    ", ""), (entry.text, text_style)))
                continue

            # User entries get extra visual weight
            if entry.kind == SessionEntryKind.USER:
                lines.append(Text(""))
                lines.append(Text.assemble(
                    (f"  {icon} ", icon_style),
                    (entry.text, text_style),
                ))
                lines.append(Text(""))
            else:
                lines.append(Text.assemble(
                    (f"  {icon} ", icon_style),
                    (entry.text, text_style),
                ))

        return Group(*lines)

    # ── result summary (post-run) ──────────────────────────────────────────

    def render_result_summary(
        self,
        *,
        rows: Iterable[tuple[str, str]],
        title: str = "Run Summary",
    ) -> RenderableType:
        """Render a clean result summary block."""
        parts: list[RenderableType] = [
            Text(""),
            Text.assemble(("  ┌─ ", "border"), (title, "section")),
        ]
        for label, value in rows:
            parts.append(Text.assemble(
                ("  │  ", "border"),
                (f"{label:<14}", "muted"),
                (value, "text"),
            ))
        parts.append(Text.assemble(("  └─", "border")))
        parts.append(Text(""))
        return Group(*parts)

    # ── legacy compose_screen (kept for runs/trace views) ──────────────────

    def compose_screen(
        self,
        *,
        mode: str,
        main: RenderableType,
        context: RenderableType,
        status_text: str,
    ) -> Layout:
        """Build the persistent header/body/status terminal layout."""
        layout = Layout(name="root")
        layout.split_column(
            Layout(name="header", size=3),
            Layout(name="body", ratio=1),
            Layout(name="status", size=3),
        )
        layout["body"].split_row(
            Layout(name="main", ratio=3),
            Layout(name="context", ratio=2, minimum_size=36),
        )
        layout["header"].update(self.render_header(mode=mode))
        layout["body"]["main"].update(main)
        layout["body"]["context"].update(context)
        layout["status"].update(self.render_status_strip(status_text))
        return layout

    def render_header(self, *, mode: str) -> Panel:
        """Render a compact header bar."""
        left = Text.assemble(("FlowForge", "title"), ("  "), (mode, "active"))
        right = Text.assemble(
            ("Ollama", "muted"),
            ("  "),
            ("qwen2.5:3b", "focus"),
            ("  "),
            ("Local Only", "muted"),
        )
        header_table = Table.grid(expand=True)
        header_table.add_column(ratio=1)
        header_table.add_column(justify="right")
        header_table.add_row(left, right)
        return Panel(header_table, border_style="border", box=box.SQUARE, padding=(0, 1))

    def render_status_strip(self, message: str) -> Panel:
        """Render the bottom status strip."""
        return Panel(Text(message, style="muted"), border_style="border", box=box.SQUARE, padding=(0, 1))

    # ── reusable components ────────────────────────────────────────────────

    def render_compact_menu(self, *, title: str, items: list[tuple[str, str]]) -> Panel:
        """Render a compact table for legacy summary and test views."""
        table = Table.grid(expand=True)
        table.add_column(style="focus", width=14)
        table.add_column(style="text")
        for key, label in items:
            table.add_row(f"[{key}]", label)
        return Panel(
            Group(Text(title, style="section"), Rule(style="border"), table),
            border_style="border",
            box=box.SQUARE,
            padding=(0, 1),
        )

    def render_context_list(self, *, title: str, rows: Iterable[tuple[str, str]]) -> Panel:
        """Render compact key/value context."""
        table = Table.grid(expand=True)
        table.add_column(style="muted", width=16)
        table.add_column(style="text")
        for label, value in rows:
            table.add_row(label, value)
        return Panel(
            Group(Text(title, style="section"), Rule(style="border"), table),
            border_style="border",
            box=box.SQUARE,
            padding=(0, 1),
        )

    def render_agent_rail(self, agents: list[tuple[str, str]]) -> Panel:
        """Render the execution status rail for all agents."""
        table = Table.grid(expand=True)
        table.add_column(style="text")
        table.add_column(justify="right")
        for name, status in agents:
            table.add_row(name, Text(status.upper(), style=self._status_style(status)))
        return Panel(
            Group(Text("Agent Rail", style="section"), Rule(style="border"), table),
            border_style="border",
            box=box.SQUARE,
            padding=(0, 1),
        )

    def render_runs_table(self, *, runs: list[dict[str, object]]) -> Panel:
        """Render a compact recent-runs table."""
        table = Table.grid(expand=True)
        table.add_column(style="focus", width=14)
        table.add_column(style="text", ratio=1)
        if not runs:
            table.add_row("-", "No runs recorded")
        else:
            for run in runs[-5:]:
                qa_value = "yes" if int(run["qa_approved"]) else "no"
                summary = f"{run['request_title']}  [{run['workflow_status']}]  QA:{qa_value}"
                table.add_row(
                    str(run["run_id"]),
                    summary,
                )
        return Panel(
            Group(Text("Recent Runs", style="section"), Rule(style="border"), table),
            border_style="border",
            box=box.SQUARE,
            padding=(0, 1),
        )

    def render_trace_preview(self, rows: list[TraceSummaryRow]) -> Panel:
        """Render a compact trace preview panel."""
        table = Table(box=box.MINIMAL, expand=True, show_edge=False, pad_edge=False)
        table.add_column("Node", style="focus")
        table.add_column("Status", style="muted")
        table.add_column("Latency", style="muted", justify="right")
        if not rows:
            table.add_row("-", "No trace data", "-")
        else:
            for row in rows[:6]:
                table.add_row(row.node_name, row.status, f"{row.latency_ms:.2f} ms")
        return Panel(
            Group(Text("Trace Preview", style="section"), Rule(style="border"), table),
            border_style="border",
            box=box.SQUARE,
            padding=(0, 1),
        )

    def render_artifacts(self, *, markdown_path: str, json_path: str, trace_path: str) -> Panel:
        """Render artifact paths in a compact structure."""
        return self.render_context_list(
            title="Artifacts",
            rows=[
                ("Markdown", markdown_path),
                ("JSON", json_path),
                ("Trace", trace_path),
            ],
        )

    @staticmethod
    def _status_style(status: str) -> str:
        mapping = {
            "pending": "muted",
            "running": "active",
            "complete": "success",
            "completed": "success",
            "blocked": "warning",
            "failed": "danger",
            "error": "danger",
        }
        return mapping.get(status.lower(), "warning")

    @staticmethod
    def _entry_style(kind: SessionEntryKind) -> tuple[str, str]:
        mapping = {
            SessionEntryKind.SYSTEM: ("system", "muted"),
            SessionEntryKind.USER: ("you", "focus"),
            SessionEntryKind.STATUS: ("status", "active"),
            SessionEntryKind.ERROR: ("error", "danger"),
            SessionEntryKind.RESULT: ("result", "success"),
        }
        return mapping.get(kind, ("line", "text"))

    @staticmethod
    def _truncate_middle(value: str, *, max_length: int) -> str:
        """Return a middle-truncated path for narrow terminal presentation."""
        if len(value) <= max_length:
            return value
        if max_length <= 7:
            return value[:max_length]
        head = (max_length - 3) // 2
        tail = max_length - 3 - head
        return f"{value[:head]}...{value[-tail:]}"
