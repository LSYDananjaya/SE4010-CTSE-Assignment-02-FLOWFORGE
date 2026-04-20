from __future__ import annotations

from collections.abc import Iterable

from rich import box
from rich.console import Group, RenderableType
from rich.columns import Columns
from rich.layout import Layout
from rich.panel import Panel
from rich.rule import Rule
from rich.table import Table
from rich.text import Text

from flowforge.launcher.models import SessionEntry, SessionEntryKind, TraceSummaryRow


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
    ) -> RenderableType:
        """Compose a minimal session frame: transcript entries flowing downward."""
        parts: list[RenderableType] = []

        # Workspace context — show a subtle line if workspace is set
        workspace = None
        for label, value in context_rows:
            if label.lower() == "workspace" and value and value != "None":
                workspace = value
                break

        if workspace:
            parts.append(
                Text.assemble(
                    ("  ◆ ", "focus"),
                    (workspace, "path"),
                )
            )
            parts.append(Text(""))

        # Transcript
        parts.append(self.render_transcript(transcript_entries))

        return Group(*parts)

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
