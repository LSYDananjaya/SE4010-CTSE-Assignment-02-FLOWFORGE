from __future__ import annotations

from pathlib import Path
from typing import Protocol

from flowforge.launcher.input_controller import AttachmentResolver, LauncherInputController
from flowforge.launcher.models import (
    RequestDraft,
    SessionCommand,
    SessionEntry,
    SessionEntryKind,
    SessionMode,
    SessionState,
)
from flowforge.launcher.project_selector import ProjectSelector
from flowforge.launcher.request_selector import RequestSelector
from flowforge.launcher.state_machine import SessionStateMachine
from flowforge.models.requests import UserRequest
from flowforge.models.state import WorkflowState
from flowforge.services.persistence import PersistenceService
from flowforge.services.reporting import ReportingService
from flowforge.services.tracing import JsonTraceWriter
from flowforge.tui.app import FlowForgeTui


class PromptIO(Protocol):
    """Minimal prompt backend used by the session controller."""

    def read_input(
        self,
        *,
        placeholder: str,
        workspace_root: Path | None = None,
        current_text: str = "",
        recent_projects: list[object] | None = None,
    ) -> str: ...


class LauncherApp:
    """Session-first terminal controller for FlowForge interactive mode."""

    def __init__(
        self,
        *,
        persistence: PersistenceService,
        reporting: ReportingService,
        trace_writer: JsonTraceWriter,
        workflow: object,
        prompt_io: PromptIO,
        sample_dir: Path,
        tui: FlowForgeTui | None = None,
    ) -> None:
        self.persistence = persistence
        self.reporting = reporting
        self.trace_writer = trace_writer
        self.workflow = workflow
        self.prompt_io = prompt_io
        self.project_selector = ProjectSelector(persistence=persistence)
        self.request_selector = RequestSelector(sample_dir=sample_dir)
        self.tui = tui or FlowForgeTui()
        self.input_controller = LauncherInputController()
        self.attachment_resolver = AttachmentResolver()
        self.state_machine = SessionStateMachine()
        self.state = self.state_machine.state

    def run(self) -> None:
        """Run the persistent session loop until the user exits."""
        while True:
            placeholder = self._placeholder_text()
            self.tui.render_session(state=self.state)
            submitted = self.prompt_io.read_input(
                placeholder=placeholder,
                workspace_root=Path(self.state.workspace_path) if self.state.workspace_path else None,
                current_text=self.state.draft_text,
                recent_projects=self.project_selector.get_recent_projects(),
            ).strip()
            self.state.draft_text = ""
            if not submitted:
                continue
            should_continue = self._handle_submission(submitted)
            if not should_continue:
                return

    def _handle_submission(self, submitted: str) -> bool:
        """Process one line of session input."""
        parsed = self.input_controller.parse_session_input(submitted)

        if self.state.mode == SessionMode.PROJECT_SELECTION and parsed.command is None:
            self._set_workspace(submitted)
            return True

        if parsed.command is not None:
            return self._handle_command(parsed.command, parsed.command_argument)

        if self.state.workspace_path is None:
            self._append_entry(
                SessionEntryKind.ERROR,
                "No workspace selected. Use /project before submitting a request.",
            )
            self.state.status_text = "Workspace required."
            return True

        self._append_entry(SessionEntryKind.USER, submitted)
        self._run_workflow(submitted)
        return True

    def _handle_command(self, command: SessionCommand, argument: str) -> bool:
        """Execute a slash command and update session state."""
        if command == SessionCommand.EXIT:
            return False
        if command == SessionCommand.HELP:
            self.state_machine.handle_command(command)
            self._append_entry(SessionEntryKind.SYSTEM, "")
            self._append_entry(SessionEntryKind.SYSTEM, "╭─ Commands ─────────────────────────────────────────╮")
            self._append_entry(SessionEntryKind.SYSTEM, "│  /project <path>   Set the workspace directory      │")
            self._append_entry(SessionEntryKind.SYSTEM, "│  /runs             View recent workflow runs         │")
            self._append_entry(SessionEntryKind.SYSTEM, "│  /new              Start a fresh request draft       │")
            self._append_entry(SessionEntryKind.SYSTEM, "│  /help             Show this help message            │")
            self._append_entry(SessionEntryKind.SYSTEM, "│  /exit             Quit FlowForge                    │")
            self._append_entry(SessionEntryKind.SYSTEM, "╰────────────────────────────────────────────────────╯")
            self._append_entry(SessionEntryKind.SYSTEM, "")
            self._append_entry(SessionEntryKind.SYSTEM, "╭─ Shortcuts ────────────────────────────────────────╮")
            self._append_entry(SessionEntryKind.SYSTEM, "│  Ctrl+P            Quick switch to /project          │")
            self._append_entry(SessionEntryKind.SYSTEM, "│  Ctrl+R            Quick switch to /runs             │")
            self._append_entry(SessionEntryKind.SYSTEM, "│  Ctrl+F            Insert @ for file attachment      │")
            self._append_entry(SessionEntryKind.SYSTEM, "│  Ctrl+L            Clear the input line              │")
            self._append_entry(SessionEntryKind.SYSTEM, "│  Tab               Accept autocomplete suggestion    │")
            self._append_entry(SessionEntryKind.SYSTEM, "╰────────────────────────────────────────────────────╯")
            self._append_entry(SessionEntryKind.SYSTEM, "")
            self._append_entry(SessionEntryKind.SYSTEM, "╭─ Usage ───────────────────────────────────────────╮")
            self._append_entry(SessionEntryKind.SYSTEM, "│  1. Set a workspace with /project <path>            │")
            self._append_entry(SessionEntryKind.SYSTEM, "│  2. Describe a bug or feature request                │")
            self._append_entry(SessionEntryKind.SYSTEM, "│  3. Use @ to attach files  (e.g. @src/app.py)        │")
            self._append_entry(SessionEntryKind.SYSTEM, "│  4. FlowForge runs 4 agents to analyze your code     │")
            self._append_entry(SessionEntryKind.SYSTEM, "╰────────────────────────────────────────────────────╯")
            self._append_entry(SessionEntryKind.SYSTEM, "")
            return True
        if command == SessionCommand.NEW:
            self.state_machine.handle_command(command)
            self.state.attachments.clear()
            self.state.draft_text = ""
            self._append_entry(SessionEntryKind.STATUS, "Started a new request draft.")
            return True
        if command == SessionCommand.RUNS:
            self.state_machine.handle_command(command)
            self._append_recent_runs()
            self.state_machine.reset_idle()
            self.state = self.state_machine.state
            return True
        if command == SessionCommand.PROJECT:
            self.state_machine.handle_command(command)
            self.state = self.state_machine.state
            if argument:
                self._set_workspace(argument)
            else:
                self._append_entry(SessionEntryKind.SYSTEM, "Enter a workspace path.")
            return True
        return True

    def _set_workspace(self, raw_path: str) -> None:
        """Validate and store the active workspace path."""
        try:
            validation = self.project_selector.validate_project_path(raw_path)
        except ValueError as error:
            self._append_entry(SessionEntryKind.ERROR, str(error))
            self.state.status_text = "Workspace selection failed."
            return
        self.state.workspace_path = validation.path
        self._remove_transcript_text("No workspace selected. Use /project to choose one.")
        self.state_machine.reset_idle()
        self.state = self.state_machine.state
        marker_text = ", ".join(validation.markers) if validation.markers else "no project markers found"
        self._append_entry(SessionEntryKind.STATUS, f"Workspace set to {validation.path} ({marker_text}).")
        self.state.status_text = "Workspace ready."

    def _append_recent_runs(self) -> None:
        """Append a compact recent-runs view into the transcript."""
        runs = self.persistence.fetch_runs()
        if not runs:
            self._append_entry(SessionEntryKind.SYSTEM, "No runs recorded yet.")
            return
        self._append_entry(SessionEntryKind.SYSTEM, "Recent runs:")
        for run in runs[-5:]:
            approved = "yes" if int(run["qa_approved"]) else "no"
            self._append_entry(
                SessionEntryKind.SYSTEM,
                f"{run['run_id']}  {run['request_title']}  [{run['workflow_status']}]  QA:{approved}",
            )

    def _run_workflow(self, submitted: str) -> None:
        """Normalize session input into a workflow request and execute it."""
        assert self.state.workspace_path is not None
        parsed = self.input_controller.parse_session_input(submitted)
        resolved = self.attachment_resolver.resolve(state=parsed, workspace_root=Path(self.state.workspace_path))
        self.state.attachments = [item.path for item in resolved]
        request = self._build_request(submitted=submitted, attachments=self.state.attachments)

        self.state_machine.handle_workflow_started()
        self.state = self.state_machine.state
        self._append_entry(SessionEntryKind.STATUS, f"Running workflow for '{request.title}'...")
        self._append_entry(SessionEntryKind.STATUS, "Waiting for Intake Agent...")
        self.state.status_text = "Waiting for Intake Agent."

        # Render with the status message before starting
        self.tui.render_session(state=self.state)

        import threading

        agent_event = threading.Event()
        pending_events: list[dict[str, object]] = []
        result_holder: dict[str, object] = {}
        error_holder: dict[str, Exception] = {}

        def _on_agent_event(event: dict[str, object]) -> None:
            pending_events.append(event)
            agent_event.set()

        # Hook into the trace writer
        old_callback = self.trace_writer.on_event
        self.trace_writer.on_event = _on_agent_event

        def _run_in_thread() -> None:
            try:
                result_holder["result"] = self.workflow.run(request)
            except Exception as exc:
                error_holder["error"] = exc
            finally:
                agent_event.set()  # Ensure main thread wakes up when done

        worker = threading.Thread(target=_run_in_thread, daemon=True)
        worker.start()

        while worker.is_alive():
            agent_event.wait(timeout=0.5)
            agent_event.clear()
            if self._drain_agent_events(pending_events):
                self.tui.render_session(state=self.state)

        worker.join()
        if self._drain_agent_events(pending_events):
            self.tui.render_session(state=self.state)

        # Restore original callback
        self.trace_writer.on_event = old_callback

        if "error" in error_holder:
            self._append_entry(SessionEntryKind.ERROR, f"Workflow failed: {error_holder['error']}")
            self.state_machine.reset_idle()
            self.state = self.state_machine.state
            self.state.status_text = "Workflow failed."
            return

        result = result_holder["result"]
        if not result.trace_file:
            result.trace_file = str(self.trace_writer.trace_path_for(result.run_id))
        artifacts = self.reporting.write_reports(result)
        self.persistence.record_run(
            run_id=result.run_id,
            request_title=result.request.title,
            workflow_status=result.workflow_status,
            qa_approved=bool(result.qa_result and result.qa_result.approved),
            artifacts=artifacts,
        )
        self.persistence.record_recent_project(self.state.workspace_path)

        self._append_result_summary(result)
        self.state_machine.reset_idle()
        self.state = self.state_machine.state
        self.state.status_text = f"Completed {result.run_id}. Reports saved to data/reports."

    def _drain_agent_events(self, pending_events: list[dict[str, object]]) -> bool:
        """Append transcript progress lines for queued trace events."""
        changed = False
        while pending_events:
            event = pending_events.pop(0)
            node_name = str(event.get("node_name", ""))
            status = str(event.get("status", ""))
            label = self._agent_label(node_name)
            latency_ms = float(event.get("latency_ms", 0.0))
            detail = str(event.get("detail", "")).strip()
            if status == "started":
                self._remove_transcript_text(f"Waiting for {label}...")
                self._append_entry(SessionEntryKind.STATUS, f"{label} started...")
                self.state.status_text = f"{label} running."
                changed = True
            elif status == "success":
                self._append_entry(SessionEntryKind.RESULT, f"{label} completed in {latency_ms:.0f}ms.")
                next_label = self._next_agent_label(node_name)
                if next_label is not None:
                    self._append_entry(SessionEntryKind.STATUS, f"Waiting for {next_label}...")
                    self.state.status_text = f"Waiting for {next_label}."
                changed = True
            elif status == "error":
                self._remove_transcript_text(f"Waiting for {label}...")
                message = f"{label} failed"
                if detail:
                    message = f"{message}: {detail}"
                self._append_entry(SessionEntryKind.ERROR, message)
                self.state.status_text = f"{label} failed."
                changed = True
        return changed

    @staticmethod
    def _agent_label(node_name: str) -> str:
        """Return a human-readable label for a workflow node."""
        return {
            "intake": "Intake Agent",
            "context": "Context Agent",
            "planning": "Planning Agent",
            "qa": "QA Agent",
        }.get(node_name, node_name)

    @staticmethod
    def _next_agent_label(node_name: str) -> str | None:
        """Return the next agent label in execution order."""
        order = ["intake", "context", "planning", "qa"]
        try:
            index = order.index(node_name)
        except ValueError:
            return None
        if index + 1 >= len(order):
            return None
        return LauncherApp._agent_label(order[index + 1])

    def _build_request(self, *, submitted: str, attachments: list[str]) -> UserRequest:
        """Convert freeform session text into a normalized workflow request."""
        assert self.state.workspace_path is not None
        title = self._derive_title(submitted)
        request_type = self._infer_request_type(submitted)
        draft = RequestDraft(
            title=title,
            request_type=request_type,
            description=submitted,
            attachments=attachments,
        )
        return self.request_selector.from_draft(draft, repo_path=self.state.workspace_path)

    def _append_result_summary(self, result: WorkflowState) -> None:
        """Append detailed workflow results to the transcript."""
        # ── Run header ──
        self._append_entry(SessionEntryKind.RESULT, f"Run {result.run_id} finished with status {result.workflow_status}.")
        self._append_entry(SessionEntryKind.SYSTEM, "")
        if result.workflow_status == "failed" and result.errors:
            self._append_entry(SessionEntryKind.ERROR, f"Failure Cause: {self._primary_failure(result.errors)}")
            self._append_entry(SessionEntryKind.SYSTEM, "")

        # ── Intake Analysis ──
        if result.intake_result:
            intake = result.intake_result
            self._append_entry(SessionEntryKind.SYSTEM, "╭─ Intake Analysis ──────────────────────────────────╮")
            self._append_entry(SessionEntryKind.SYSTEM, f"│  Category:  {intake.category:<10}  Severity: {intake.severity:<10}│")
            self._append_entry(SessionEntryKind.SYSTEM, f"│  Scope:     {intake.scope:<40}│")
            self._append_entry(SessionEntryKind.SYSTEM, f"│  Summary:   {intake.summary[:40]:<40}│")
            if intake.goals:
                self._append_entry(SessionEntryKind.SYSTEM, f"│  Goals:     {', '.join(intake.goals[:3])[:40]:<40}│")
            if intake.missing_information:
                self._append_entry(SessionEntryKind.SYSTEM, f"│  Missing:   {', '.join(intake.missing_information[:2])[:40]:<40}│")
            self._append_entry(SessionEntryKind.SYSTEM, "╰────────────────────────────────────────────────────╯")
            self._append_entry(SessionEntryKind.SYSTEM, "")

        # ── Context Snippets ──
        if result.context_bundle:
            ctx = result.context_bundle
            self._append_entry(SessionEntryKind.SYSTEM, f"╭─ Context ({len(ctx.selected_snippets)} snippets from {ctx.files_considered} files) ──╮")
            for snippet in ctx.selected_snippets[:6]:
                self._append_entry(SessionEntryKind.SYSTEM, f"│  📄 {snippet.path}")
                self._append_entry(SessionEntryKind.SYSTEM, f"│     └─ {snippet.reason[:50]}")
            self._append_entry(SessionEntryKind.SYSTEM, "╰────────────────────────────────────────────────────╯")
            self._append_entry(SessionEntryKind.SYSTEM, "")

        # ── Implementation Plan ──
        if result.plan_result:
            plan = result.plan_result
            self._append_entry(SessionEntryKind.SYSTEM, f"╭─ Implementation Plan ({len(plan.tasks)} tasks) ─────────────╮")
            if plan.summary:
                self._append_entry(SessionEntryKind.SYSTEM, f"│  {plan.summary[:52]}")
            self._append_entry(SessionEntryKind.SYSTEM, "│")
            for task in plan.tasks:
                prio_icon = {"high": "🔴", "medium": "🟡", "low": "🟢"}.get(task.priority, "⚪")
                self._append_entry(SessionEntryKind.SYSTEM, f"│  {prio_icon} {task.task_id}: {task.title}")
                self._append_entry(SessionEntryKind.SYSTEM, f"│     Priority: {task.priority}  │  Owner: {task.owner}")
                if task.description:
                    desc_preview = task.description[:60] + ("..." if len(task.description) > 60 else "")
                    self._append_entry(SessionEntryKind.SYSTEM, f"│     {desc_preview}")
                if task.acceptance_criteria:
                    for ac in task.acceptance_criteria[:3]:
                        self._append_entry(SessionEntryKind.SYSTEM, f"│     ✅ {ac[:55]}")
                if task.risks:
                    for risk in task.risks[:2]:
                        self._append_entry(SessionEntryKind.SYSTEM, f"│     ⚠️  {risk[:55]}")
                if task.dependencies:
                    self._append_entry(SessionEntryKind.SYSTEM, f"│     Deps: {', '.join(task.dependencies)}")
                self._append_entry(SessionEntryKind.SYSTEM, "│")

            if plan.overall_risks:
                self._append_entry(SessionEntryKind.SYSTEM, "│  Overall Risks:")
                for risk in plan.overall_risks[:3]:
                    self._append_entry(SessionEntryKind.SYSTEM, f"│     ⚠️  {risk[:55]}")
            self._append_entry(SessionEntryKind.SYSTEM, "╰────────────────────────────────────────────────────╯")
            self._append_entry(SessionEntryKind.SYSTEM, "")

        # ── QA Verdict ──
        if result.qa_result:
            qa = result.qa_result
            verdict = "✅ APPROVED" if qa.approved else "⚠️  NEEDS REVIEW"
            self._append_entry(SessionEntryKind.SYSTEM, f"╭─ QA Verdict: {verdict} ─────────────────────────╮")
            if qa.summary:
                self._append_entry(SessionEntryKind.SYSTEM, f"│  {qa.summary[:52]}")
            if qa.findings:
                for finding in qa.findings[:4]:
                    self._append_entry(SessionEntryKind.SYSTEM, f"│  • {finding[:52]}")
            if qa.rubric_checks:
                self._append_entry(SessionEntryKind.SYSTEM, "│")
                for check, passed in qa.rubric_checks.items():
                    icon = "✓" if passed else "✗"
                    self._append_entry(SessionEntryKind.SYSTEM, f"│  {icon} {check}")
            self._append_entry(SessionEntryKind.SYSTEM, "╰────────────────────────────────────────────────────╯")
            self._append_entry(SessionEntryKind.SYSTEM, "")

        # ── Trace Timing Table ──
        if result.trace_file:
            trace_rows = self.trace_writer.read_trace_summary(Path(result.trace_file))
            if trace_rows:
                self._append_entry(SessionEntryKind.SYSTEM, "╭─ Trace ────────────────────────────────────────────╮")
                self._append_entry(SessionEntryKind.SYSTEM, "│  Agent            Status       Latency             │")
                self._append_entry(SessionEntryKind.SYSTEM, "│  ─────────────    ──────       ───────             │")
                total_ms = 0.0
                for row in trace_rows:
                    s_icon = "✓" if row.status == "success" else "✗"
                    latency_str = f"{row.latency_ms:>8.0f}ms"
                    self._append_entry(
                        SessionEntryKind.SYSTEM,
                        f"│  {s_icon} {row.node_name:<15} {row.status:<12} {latency_str}  │",
                    )
                    total_ms += row.latency_ms
                self._append_entry(SessionEntryKind.SYSTEM, "│  ─────────────    ──────       ───────             │")
                self._append_entry(SessionEntryKind.SYSTEM, f"│  Total                         {total_ms:>8.0f}ms  │")
                self._append_entry(SessionEntryKind.SYSTEM, "╰────────────────────────────────────────────────────╯")
                self._append_entry(SessionEntryKind.SYSTEM, "")

        # ── Artifact Paths ──
        if result.artifacts:
            self._append_entry(SessionEntryKind.SYSTEM, "╭─ Reports ──────────────────────────────────────────╮")
            self._append_entry(SessionEntryKind.SYSTEM, f"│  📝 {result.artifacts.markdown_report}")
            self._append_entry(SessionEntryKind.SYSTEM, f"│  📋 {result.artifacts.json_report}")
            self._append_entry(SessionEntryKind.SYSTEM, f"│  📊 {result.artifacts.trace_file}")
            self._append_entry(SessionEntryKind.SYSTEM, "╰────────────────────────────────────────────────────╯")

    def _append_entry(self, kind: SessionEntryKind, text: str) -> None:
        """Append one transcript line."""
        self.state.transcript.append(SessionEntry(kind=kind, text=text))

    def _remove_transcript_text(self, text: str) -> None:
        """Remove stale transcript lines that no longer match the session state."""
        self.state.transcript = [entry for entry in self.state.transcript if entry.text != text]

    @staticmethod
    def _primary_failure(errors: list[str]) -> str:
        """Return the most useful root-cause error for a failed run."""
        for error in errors:
            if not error.endswith("Agent failed.") and "requires intake" not in error:
                return error
        return errors[0]

    def _placeholder_text(self) -> str:
        """Return the prompt placeholder for the current session mode."""
        if self.state.mode == SessionMode.PROJECT_SELECTION:
            return "Enter a workspace path..."
        return "Describe a bug or feature request..."

    @staticmethod
    def _derive_title(submitted: str) -> str:
        """Derive a compact request title from freeform session input."""
        cleaned = submitted.replace("@", "").strip()
        title_words = cleaned.split()
        title = " ".join(title_words[:8]).strip()
        if not title:
            return "Session request"
        if len(title) < 3:
            return f"{title} request"
        return title[:80]

    @staticmethod
    def _infer_request_type(submitted: str) -> str:
        """Infer bug vs feature from freeform session input."""
        lowered = submitted.lower()
        feature_markers = (
            "improvement",
            "improvements",
            "improve",
            "suggest",
            "suggestion",
            "review",
            "feature",
            "enhancement",
            "add",
            "what can i improve",
        )
        bug_markers = (
            "bug",
            "fix",
            "broken",
            "issue",
            "error",
            "fail",
            "failing",
            "crash",
            "timeout",
            "not working",
            "doesn't work",
            "does not work",
        )
        if any(marker in lowered for marker in feature_markers) and not any(marker in lowered for marker in bug_markers):
            return "feature"
        return "bug" if any(marker in lowered for marker in bug_markers) else "feature"
