from __future__ import annotations

from pathlib import Path

from flowforge.launcher.input_controller import AttachmentResolver, LauncherInputController
from flowforge.launcher.models import (
    AttachmentToken,
    SessionCommand,
    SessionInputState,
    SuggestionCandidate,
)


def test_parse_freeform_input_without_mentions() -> None:
    controller = LauncherInputController()

    state = controller.parse_session_input("write a plan for login timeout")

    assert state.raw_text == "write a plan for login timeout"
    assert state.attachments == []
    assert state.command is None



def test_parse_session_command_and_argument() -> None:
    controller = LauncherInputController()

    state = controller.parse_session_input("/project C:/repos/sample")

    assert state.command == SessionCommand.PROJECT
    assert state.command_argument == "C:/repos/sample"


def test_parse_input_detects_at_mentions() -> None:
    controller = LauncherInputController()

    state = controller.parse_session_input("analyze @src/auth_service.py and @README.md")

    assert [token.path for token in state.attachments] == ["src/auth_service.py", "README.md"]


def test_insert_suggestion_replaces_active_mention() -> None:
    controller = LauncherInputController()
    state = SessionInputState(raw_text="inspect @src/aut", cursor_position=len("inspect @src/aut"))

    updated = controller.apply_suggestion(
        state,
        SuggestionCandidate(display="src/auth_service.py", value="src/auth_service.py"),
    )

    assert updated.raw_text == "inspect @src/auth_service.py"


def test_attachment_resolver_uses_workspace_only(sample_repo: Path) -> None:
    resolver = AttachmentResolver()
    state = SessionInputState(
        raw_text="inspect @src/auth_service.py",
        attachments=[AttachmentToken(path="src/auth_service.py", start=8, end=28)],
        cursor_position=28,
    )

    resolved = resolver.resolve(state=state, workspace_root=sample_repo)

    assert len(resolved) == 1
    assert resolved[0].path == "src/auth_service.py"
    assert "def login" in resolved[0].content


def test_attachment_resolver_supports_external_repo_root(tmp_path: Path) -> None:
    external_repo = tmp_path / "external" / "mobile-app"
    component_path = external_repo / "src" / "components"
    component_path.mkdir(parents=True)
    (component_path / "CategoryPicker.tsx").write_text(
        "export function CategoryPicker() {\n"
        "  return null;\n"
        "}\n",
        encoding="utf-8",
    )
    resolver = AttachmentResolver()
    state = SessionInputState(
        raw_text="review @src/components/CategoryPicker.tsx",
        attachments=[AttachmentToken(path="src/components/CategoryPicker.tsx", start=7, end=40)],
        cursor_position=40,
    )

    resolved = resolver.resolve(state=state, workspace_root=external_repo)

    assert len(resolved) == 1
    assert resolved[0].path == "src/components/CategoryPicker.tsx"
    assert resolved[0].absolute_path == str((component_path / "CategoryPicker.tsx").resolve())
