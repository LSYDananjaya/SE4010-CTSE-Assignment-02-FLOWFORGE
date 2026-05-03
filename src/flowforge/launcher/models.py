from __future__ import annotations

from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, Field

from flowforge.models.outputs import ArtifactPaths, ContextBundle, IntakeResult, PlanResult, QaResult


class SessionMode(StrEnum):
    """High-level modes for the interactive session UI."""

    IDLE = "Idle"
    PROJECT_SELECTION = "Project Selection"
    RECENT_RUNS = "Recent Runs"
    RUNNING = "Running"


class SessionCommand(StrEnum):
    """Supported slash commands for the session prompt."""

    PROJECT = "/project"
    RUNS = "/runs"
    NEW = "/new"
    HELP = "/help"
    EXIT = "/exit"


class SessionEntryKind(StrEnum):
    """Transcript line categories for session rendering."""

    SYSTEM = "system"
    USER = "user"
    STATUS = "status"
    ERROR = "error"
    RESULT = "result"
    ASSISTANT = "assistant"


class LauncherMode(StrEnum):
    """High-level modes for the interactive launcher."""

    WELCOME = "Welcome"
    LAUNCHER = "Launcher"
    PROJECT_PICKER = "Project Picker"
    RECENT_RUNS = "Recent Runs"
    REQUEST_DRAFT = "Request Draft"


class LauncherCommand(StrEnum):
    """Parsed launcher command categories."""

    SUBMIT_REQUEST = "submit_request"
    ATTACH_FILE = "attach_file"
    OPEN_PROJECTS = "open_projects"
    OPEN_RECENT_RUNS = "open_recent_runs"


class SessionEntry(BaseModel):
    """Single transcript line displayed in the session view."""

    kind: SessionEntryKind
    text: str


class RecentProject(BaseModel):
    """Stored recent-project metadata for launcher reuse."""

    path: str
    label: str


class DirectoryChoice(BaseModel):
    """Single directory option shown in the interactive browser."""

    key: str
    label: str
    path: str
    kind: Literal["parent", "directory", "current"]


class ProjectValidation(BaseModel):
    """Validation result for a selected project path."""

    path: str
    exists: bool
    is_directory: bool
    project_like: bool
    markers: list[str] = Field(default_factory=list)


class RequestDraft(BaseModel):
    """Terminal-authored request prior to conversion into a workflow request."""

    title: str
    request_type: Literal["bug", "feature"]
    description: str
    constraints: list[str] = Field(default_factory=list)
    reporter: str = Field(default="unknown")
    attachments: list[str] = Field(default_factory=list)


class AttachmentToken(BaseModel):
    """Resolved mention token found inside launcher input."""

    path: str
    start: int
    end: int


class ResolvedAttachment(BaseModel):
    """Resolved workspace attachment content."""

    path: str
    absolute_path: str
    content: str


class SuggestionCandidate(BaseModel):
    """Suggestion entry displayed for file attachment completion."""

    display: str
    value: str
    meta: str = ""


class SuggestionMatchSet(BaseModel):
    """Full suggestion result including visible items and total match count."""

    candidates: list[SuggestionCandidate] = Field(default_factory=list)
    total_count: int = 0


class PromptSuggestionState(BaseModel):
    """Transient @-suggestion state for the interactive prompt."""

    active: bool = False
    mode: Literal["file", "command", "none"] = "none"
    query: str = ""
    candidates: list[SuggestionCandidate] = Field(default_factory=list)
    total_count: int = 0
    selected_index: int = 0
    scroll_offset: int = 0


class AgentProgressEntry(BaseModel):
    """Live launcher progress state for a single agent."""

    name: str
    status: Literal["pending", "running", "completed", "failed", "blocked"] = "pending"
    detail: str = ""


class SessionRunHistoryEntry(BaseModel):
    """Collapsed summary of a previously completed workflow run."""

    run_id: str
    title: str
    status: str
    summary: str = ""


class SessionRunDetail(BaseModel):
    """Latest workflow result displayed in the dedicated output section."""

    run_id: str
    title: str
    status: str
    trace_rows: list["TraceSummaryRow"] = Field(default_factory=list)
    intake_result: "IntakeResult | None" = None
    context_bundle: "ContextBundle | None" = None
    plan_result: "PlanResult | None" = None
    qa_result: "QaResult | None" = None
    artifacts: "ArtifactPaths | None" = None
    failure_cause: str = ""


class SessionInputState(BaseModel):
    """Current interactive prompt state."""

    raw_text: str
    cursor_position: int
    command: SessionCommand | None = None
    command_argument: str = ""
    attachments: list[AttachmentToken] = Field(default_factory=list)
    selected_index: int = 0


class LauncherInputState(SessionInputState):
    """Backward-compatible alias for older launcher tests."""


class ShortcutHint(BaseModel):
    """Visible keyboard hint entry for the launcher footer."""

    key: str
    label: str


class LauncherState(BaseModel):
    """High-level launcher state for screen transitions."""

    mode: LauncherMode
    selected_project: str | None = None
    status_text: str = "Ready"


class SessionState(BaseModel):
    """Shared state for the session-first interactive UI."""

    mode: SessionMode = SessionMode.IDLE
    transcript: list[SessionEntry] = Field(default_factory=list)
    workspace_path: str | None = None
    workspace_markers: list[str] = Field(default_factory=list)
    attachments: list[str] = Field(default_factory=list)
    agent_progress: list[AgentProgressEntry] = Field(default_factory=list)
    current_run: SessionRunDetail | None = None
    run_history: list[SessionRunHistoryEntry] = Field(default_factory=list)
    workflow_active: bool = False
    status_text: str = "/project  /runs  /new  /help"
    draft_text: str = ""

    @classmethod
    def initial(cls) -> "SessionState":
        """Create the initial transcript shown on startup."""
        return cls(
            transcript=[
                SessionEntry(kind=SessionEntryKind.SYSTEM, text="No workspace selected. Use /project to choose one."),
            ]
        )


class TraceSummaryRow(BaseModel):
    """Compact view of a trace event for launcher previews."""

    node_name: str
    status: str
    latency_ms: float
