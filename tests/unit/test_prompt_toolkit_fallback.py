from __future__ import annotations

import sys

from flowforge.launcher.prompt_toolkit_io import PromptSuggestionController, PromptToolkitPromptIO, prompt_toolkit_available
from flowforge.launcher.models import SuggestionCandidate


def test_prompt_toolkit_availability_returns_boolean() -> None:
    result = prompt_toolkit_available()
    assert isinstance(result, bool)


def test_prompt_suggestion_controller_detects_active_at_query(sample_repo) -> None:
    controller = PromptSuggestionController()

    state = controller.build_state(
        text="find a @src/au",
        cursor_position=len("find a @src/au"),
        workspace_root=sample_repo,
    )

    assert state.active is True
    assert state.mode == "file"
    assert state.query == "src/au"
    assert state.total_count >= 1


def test_prompt_suggestion_controller_formats_bottom_pager(sample_repo) -> None:
    controller = PromptSuggestionController()

    state = controller.build_state(
        text="@",
        cursor_position=1,
        workspace_root=sample_repo,
    )

    assert controller.pager_text(state).startswith("(")
    assert "/" in controller.pager_text(state)


def test_prompt_suggestion_controller_wraps_selection(sample_repo) -> None:
    controller = PromptSuggestionController()
    state = controller.build_state(
        text="@",
        cursor_position=1,
        workspace_root=sample_repo,
    )

    wrapped = controller.move_selection(state, "up")

    assert wrapped.selected_index == wrapped.total_count - 1


def test_prompt_suggestion_controller_detects_slash_command_mode() -> None:
    controller = PromptSuggestionController()

    state = controller.build_state(
        text="/pr",
        cursor_position=len("/pr"),
        workspace_root=None,
    )

    assert state.active is True
    assert state.mode == "command"
    assert state.total_count >= 1
    assert state.candidates[0].value.startswith("/p")


def test_prompt_suggestion_controller_does_not_hide_pager_when_many_files(sample_repo) -> None:
    controller = PromptSuggestionController(visible_limit=7)

    state = controller.build_state(
        text="@",
        cursor_position=1,
        workspace_root=sample_repo,
    )

    assert len(controller.visible_candidates(state)) <= 7
    assert controller.pager_text(state).startswith("(")


def test_prompt_suggestion_controller_applies_slash_candidate() -> None:
    controller = PromptSuggestionController()

    updated_text, updated_cursor = controller.apply_candidate(
        text="/pr",
        cursor_position=3,
        candidate=SuggestionCandidate(display="/project", value="/project", meta="Set workspace directory"),
        mode="command",
    )

    assert updated_text == "/project"
    assert updated_cursor == len("/project")


def test_prompt_suggestion_controller_submits_slash_candidate_on_enter() -> None:
    controller = PromptSuggestionController()
    state = controller.build_state(
        text="/pr",
        cursor_position=3,
        workspace_root=None,
    )

    assert controller.should_submit_on_enter(state) is True
    assert controller.submit_candidate(state.candidates[state.selected_index], mode=state.mode) == "/project"


def test_prompt_suggestion_controller_finalizes_file_candidate_with_trailing_space(sample_repo) -> None:
    controller = PromptSuggestionController()
    state = controller.build_state(
        text="review @src/auth",
        cursor_position=len("review @src/auth"),
        workspace_root=sample_repo,
    )

    updated_text, updated_cursor = controller.apply_candidate(
        text="review @src/auth",
        cursor_position=len("review @src/auth"),
        candidate=state.candidates[state.selected_index],
        mode=state.mode,
    )

    assert updated_text.endswith("@src/auth_service.py ")
    assert updated_cursor == len(updated_text)


def test_prompt_suggestion_controller_closes_file_picker_after_finalized_insert(sample_repo) -> None:
    controller = PromptSuggestionController()
    updated_text = "review @src/auth_service.py "
    state = controller.build_state(
        text=updated_text,
        cursor_position=len(updated_text),
        workspace_root=sample_repo,
    )

    assert state.active is False


def test_prompt_toolkit_prompt_io_builds_application_without_name_error(monkeypatch) -> None:
    prompt_io = PromptToolkitPromptIO()

    class FakeApplication:
        def __init__(self, *args, **kwargs) -> None:  # type: ignore[no-untyped-def]
            pass

        def run(self) -> str:
            return ""

    monkeypatch.setattr("prompt_toolkit.application.Application", FakeApplication)

    result = prompt_io.read_input(placeholder="Describe a bug or feature request...")

    assert result == ""
