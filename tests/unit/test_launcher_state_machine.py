from __future__ import annotations

from flowforge.launcher.models import SessionCommand, SessionMode
from flowforge.launcher.state_machine import SessionStateMachine


def test_project_and_runs_commands_change_session_mode() -> None:
    machine = SessionStateMachine()

    machine.handle_command(SessionCommand.PROJECT)
    assert machine.state.mode == SessionMode.PROJECT_SELECTION

    machine.handle_command(SessionCommand.RUNS)
    assert machine.state.mode == SessionMode.RECENT_RUNS


def test_running_and_reset_return_session_to_idle() -> None:
    machine = SessionStateMachine()

    machine.handle_workflow_started()
    assert machine.state.mode == SessionMode.RUNNING

    machine.handle_command(SessionCommand.NEW)
    assert machine.state.mode == SessionMode.IDLE
