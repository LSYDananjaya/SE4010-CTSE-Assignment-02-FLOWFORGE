from __future__ import annotations

from flowforge.launcher.models import SessionCommand, SessionMode, SessionState


class SessionStateMachine:
    """Minimal state machine for the session-first interactive UI."""

    def __init__(self) -> None:
        self.state = SessionState.initial()

    def handle_command(self, command: SessionCommand) -> SessionState:
        """Transition high-level session mode based on a slash command."""
        match command:
            case SessionCommand.PROJECT:
                self.state.mode = SessionMode.PROJECT_SELECTION
                self.state.status_text = "Enter a workspace path. Tab completes directories."
            case SessionCommand.RUNS:
                self.state.mode = SessionMode.RECENT_RUNS
                self.state.status_text = "Showing recent runs."
            case SessionCommand.NEW | SessionCommand.HELP | SessionCommand.EXIT:
                self.state.mode = SessionMode.IDLE
                self.state.status_text = "/project  /runs  /new  /help"
        return self.state

    def handle_workflow_started(self) -> SessionState:
        """Enter the running state while the workflow executes."""
        self.state.mode = SessionMode.RUNNING
        self.state.status_text = "Workflow running."
        return self.state

    def reset_idle(self) -> SessionState:
        """Return to the default idle mode after a command or run completes."""
        self.state.mode = SessionMode.IDLE
        self.state.status_text = "/project  /runs  /new  /help"
        return self.state

