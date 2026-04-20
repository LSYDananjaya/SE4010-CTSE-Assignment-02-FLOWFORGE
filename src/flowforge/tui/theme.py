from __future__ import annotations

from rich.console import Console, Group
from rich.panel import Panel
from rich.rule import Rule
from rich.table import Table
from rich.text import Text
from rich.theme import Theme


FLOWFORGE_THEME = Theme(
    {
        # ── base text ──
        "title": "bold #e2e8f0",
        "section": "bold #cbd5e1",
        "text": "#94a3b8",
        "muted": "#64748b",
        "placeholder": "#475569",
        # ── accents ──
        "focus": "bold #22d3ee",
        "active": "bold #38bdf8",
        "success": "bold #34d399",
        "warning": "bold #fbbf24",
        "danger": "bold #f87171",
        # ── structural ──
        "border": "#334155",
        "path": "#7dd3fc",
        "badge": "bold #2dd4bf",
        # ── transcript entry styles ──
        "entry.system": "italic #64748b",
        "entry.user": "bold #22d3ee",
        "entry.status": "#38bdf8",
        "entry.error": "bold #f87171",
        "entry.result": "bold #34d399",
        "entry.assistant": "#e2e8f0",
        # ── prompt ──
        "prompt.indicator": "bold #22d3ee",
        "toolbar": "#475569",
        "toolbar.key": "#94a3b8",
        # ── banner ──
        "banner.art": "bold #22d3ee",
        "banner.border": "#f97316",
        "banner.tip.title": "bold #f97316",
        "banner.tip": "#94a3b8",
    }
)

# ── Brick-style ASCII art ──────────────────────────────────────────────────────
# Each letter is 5 lines tall, using solid block characters for a clean look.

_LETTER_ART: dict[str, list[str]] = {
    "F": [
        "████████",
        "██      ",
        "██████  ",
        "██      ",
        "██      ",
    ],
    "L": [
        "██      ",
        "██      ",
        "██      ",
        "██      ",
        "████████",
    ],
    "O": [
        " ██████ ",
        "██    ██",
        "██    ██",
        "██    ██",
        " ██████ ",
    ],
    "W": [
        "██      ██",
        "██  ██  ██",
        "██  ██  ██",
        "██ ████ ██",
        " ███  ███ ",
    ],
    "R": [
        "███████ ",
        "██    ██",
        "███████ ",
        "██  ██  ",
        "██    ██",
    ],
    "G": [
        " ██████ ",
        "██      ",
        "██  ████",
        "██    ██",
        " ██████ ",
    ],
    "E": [
        "████████",
        "██      ",
        "██████  ",
        "██      ",
        "████████",
    ],
}


def _build_ascii_title(word: str = "FLOWFORGE") -> list[str]:
    """Assemble brick-style ASCII art for the given word."""
    num_rows = 5
    rows = [""] * num_rows
    for i, ch in enumerate(word.upper()):
        art = _LETTER_ART.get(ch)
        if art is None:
            art = [" " * 4] * num_rows
        for r in range(num_rows):
            rows[r] += art[r] + "  "
    return rows


def build_console(*, record: bool = False) -> Console:
    """Create a themed Rich console."""
    return Console(theme=FLOWFORGE_THEME, record=record)


def render_banner(*, model: str = "qwen2.5:3b", provider: str = "Ollama", workspace: str | None = None) -> Group:
    """Render a Claude Code-style welcome banner with large ASCII art title."""
    parts: list[Text | Rule] = []

    # ── Large ASCII art title ──
    ascii_rows = _build_ascii_title("FLOWFORGE")
    parts.append(Text(""))
    for row in ascii_rows:
        parts.append(Text(f"  {row}", style="banner.art"))
    parts.append(Text(""))

    # ── Info line ──
    parts.append(Text.assemble(
        ("  ", ""),
        (provider, "muted"),
        (" · ", "border"),
        (model, "bold #e2e8f0"),
        (" · ", "border"),
        ("Local Only", "muted"),
    ))

    if workspace:
        parts.append(Text.assemble(
            ("  ", ""),
            (workspace, "path"),
        ))

    parts.append(Text(""))

    # ── Tips panel ──
    parts.append(Text.assemble(("  ", ""), ("Tips for getting started", "banner.tip.title")))
    parts.append(Text.assemble(("  ", ""), ("Use ", "banner.tip"), ("/project <path>", "bold #94a3b8"), (" to set the workspace directory", "banner.tip")))
    parts.append(Text.assemble(("  ", ""), ("Use ", "banner.tip"), ("@", "focus"), (" to attach workspace files for context", "banner.tip")))
    parts.append(Text.assemble(("  ", ""), ("Type ", "banner.tip"), ("/help", "bold #94a3b8"), (" for all commands and shortcuts", "banner.tip")))
    parts.append(Text(""))

    # ── Separator ──
    parts.append(Rule(style="border"))
    parts.append(Text(""))

    return Group(*parts)


def render_status_panel(*, title: str, status: str, body: str) -> Panel:
    """Render a status panel with explicit text and color."""
    status_upper = status.upper()
    status_style = {
        "pending": "muted",
        "running": "active",
        "complete": "success",
        "completed": "success",
        "failed": "danger",
        "error": "danger",
    }.get(status.lower(), "warning")
    return Panel(
        Group(Text(f"{status_upper}", style=status_style), Text(body, style="muted")),
        title=f"[title]{title}[/title]",
        border_style=status_style,
    )


def render_welcome_panel() -> Panel:
    """Render the launcher welcome panel (legacy compat)."""
    body = Group(
        Text("FlowForge", style="title"),
        Text("Local multi-agent workflow launcher", style="text"),
        Text("Ollama • qwen2.5:3b • LangGraph • 4 agents", style="muted"),
    )
    return Panel(body, title="[section]Launcher[/section]", border_style="border")


def render_artifact_table(*, markdown_path: str, json_path: str, trace_path: str) -> Table:
    """Render a colorized artifact table."""
    table = Table(title="Artifacts", title_style="section")
    table.add_column("Type", style="muted")
    table.add_column("Path", style="path")
    table.add_row("Markdown", markdown_path)
    table.add_row("JSON", json_path)
    table.add_row("Trace", trace_path)
    return table
