from __future__ import annotations

import re
from pathlib import Path

from flowforge.launcher.models import (
    AttachmentToken,
    ResolvedAttachment,
    SessionCommand,
    SessionInputState,
    SuggestionCandidate,
)


MENTION_PATTERN = re.compile(r"@(?P<path>[^\s@]+)")
COMMAND_PATTERN = re.compile(r"^(?P<command>/[a-z]+)(?:\s+(?P<argument>.+))?$")


class LauncherInputController:
    """Parse, mutate, and normalize the single launcher input field."""

    def parse_session_input(self, text: str, cursor_position: int | None = None) -> SessionInputState:
        """Parse session input into commands, attachments, and cursor state."""
        attachments = [
            AttachmentToken(
                path=match.group("path"),
                start=match.start(),
                end=match.end(),
            )
            for match in MENTION_PATTERN.finditer(text)
        ]
        command: SessionCommand | None = None
        command_argument = ""
        command_match = COMMAND_PATTERN.match(text.strip())
        if command_match is not None:
            raw_command = command_match.group("command")
            try:
                command = SessionCommand(raw_command)
            except ValueError:
                command = None
            command_argument = (command_match.group("argument") or "").strip()
        return SessionInputState(
            raw_text=text,
            cursor_position=len(text) if cursor_position is None else cursor_position,
            command=command,
            command_argument=command_argument,
            attachments=attachments,
        )

    def parse_input(self, text: str, cursor_position: int | None = None) -> SessionInputState:
        """Backward-compatible wrapper for earlier launcher tests."""
        return self.parse_session_input(text, cursor_position=cursor_position)

    def apply_suggestion(
        self,
        state: SessionInputState,
        suggestion: SuggestionCandidate,
        *,
        finalize: bool = False,
    ) -> SessionInputState:
        """Replace the active partial mention with the selected suggestion."""
        before_cursor = state.raw_text[: state.cursor_position]
        marker_index = before_cursor.rfind("@")
        if marker_index < 0:
            return state
        suffix = " " if finalize else ""
        updated_text = f"{state.raw_text[:marker_index]}@{suggestion.value}{suffix}{state.raw_text[state.cursor_position:]}"
        new_cursor = marker_index + len(suggestion.value) + 1 + len(suffix)
        return self.parse_session_input(updated_text, cursor_position=new_cursor)


class AttachmentResolver:
    """Resolve launcher attachment tokens into workspace file references."""

    def resolve(self, *, state: SessionInputState, workspace_root: Path) -> list[ResolvedAttachment]:
        """Resolve mentioned files only from the selected workspace."""
        resolved: list[ResolvedAttachment] = []
        for token in state.attachments:
            candidate = (workspace_root / token.path).resolve()
            if not str(candidate).startswith(str(workspace_root.resolve())):
                continue
            if not candidate.exists() or not candidate.is_file():
                continue
            content = candidate.read_text(encoding="utf-8", errors="ignore")
            resolved.append(
                ResolvedAttachment(
                    path=token.path,
                    absolute_path=str(candidate),
                    content=content[:1000],
                )
            )
        return resolved
