from __future__ import annotations

from pathlib import Path

try:
    from prompt_toolkit.completion import Completer as _Completer
except ModuleNotFoundError:  # pragma: no cover
    _Completer = object  # type: ignore[misc,assignment]

from flowforge.launcher.file_suggester import FileSuggester
from flowforge.launcher.models import RecentProject, SessionCommand


def prompt_toolkit_available() -> bool:
    """Return whether prompt_toolkit can be imported in the active interpreter."""
    try:
        import prompt_toolkit  # noqa: F401
    except ModuleNotFoundError:
        return False
    return True


class PromptToolkitPromptIO:
    """Keyboard-first prompt backend for the session-style interface."""

    def __init__(self) -> None:
        self.file_suggester = FileSuggester()

    def read_input(
        self,
        *,
        placeholder: str,
        workspace_root: Path | None = None,
        current_text: str = "",
        recent_projects: list[RecentProject] | None = None,
    ) -> str:
        """Read a single session prompt with inline completions and shortcuts."""
        from prompt_toolkit import PromptSession
        from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
        from prompt_toolkit.history import InMemoryHistory
        from prompt_toolkit.key_binding import KeyBindings
        from prompt_toolkit.styles import Style

        history = InMemoryHistory()
        completer = SessionCompleter(
            file_suggester=self.file_suggester,
            workspace_root=workspace_root,
            recent_projects=recent_projects or [],
        )

        bindings = KeyBindings()

        @bindings.add("c-p")
        def _project(event) -> None:  # type: ignore[no-untyped-def]
            event.app.current_buffer.text = f"{SessionCommand.PROJECT.value} "
            event.app.current_buffer.cursor_position = len(event.app.current_buffer.text)

        @bindings.add("c-r")
        def _runs(event) -> None:  # type: ignore[no-untyped-def]
            event.app.current_buffer.text = SessionCommand.RUNS.value
            event.app.current_buffer.cursor_position = len(event.app.current_buffer.text)

        @bindings.add("c-l")
        def _clear(event) -> None:  # type: ignore[no-untyped-def]
            event.app.current_buffer.text = ""
            event.app.current_buffer.cursor_position = 0

        @bindings.add("c-f")
        def _attach(event) -> None:  # type: ignore[no-untyped-def]
            insertion = "@"
            event.app.current_buffer.insert_text(insertion)

        def _bottom_toolbar() -> list[tuple[str, str]]:
            return [
                ("class:toolbar.bg", " "),
                ("class:toolbar.cmd", " /project"),
                ("class:toolbar.sep", " │ "),
                ("class:toolbar.cmd", "/runs"),
                ("class:toolbar.sep", " │ "),
                ("class:toolbar.cmd", "/new"),
                ("class:toolbar.sep", " │ "),
                ("class:toolbar.cmd", "/help"),
                ("class:toolbar.sep", " │ "),
                ("class:toolbar.cmd", "/exit"),
                ("class:toolbar.sep", "   ·   "),
                ("class:toolbar.key", "Tab "),
                ("class:toolbar.hint", "accept  "),
                ("class:toolbar.key", "Ctrl+P "),
                ("class:toolbar.hint", "project  "),
                ("class:toolbar.key", "Ctrl+F "),
                ("class:toolbar.hint", "attach  "),
                ("class:toolbar.key", "@ "),
                ("class:toolbar.hint", "file "),
            ]

        pt_style = Style.from_dict({
            "prompt": "bold #22d3ee",
            "": "#94a3b8",
            "bottom-toolbar": "bg:#0f172a #475569",
            "toolbar.bg": "bg:#0f172a",
            "toolbar.cmd": "bg:#0f172a #94a3b8",
            "toolbar.sep": "bg:#0f172a #334155",
            "toolbar.key": "bg:#0f172a bold #cbd5e1",
            "toolbar.hint": "bg:#0f172a #64748b",
            "placeholder": "#475569 italic",
        })

        session = PromptSession(
            completer=completer,
            complete_while_typing=True,
            auto_suggest=AutoSuggestFromHistory(),
            key_bindings=bindings,
            history=history,
            reserve_space_for_menu=6,
            bottom_toolbar=_bottom_toolbar,
            style=pt_style,
        )

        prompt_message = [("class:prompt", "❯ ")]

        return session.prompt(prompt_message, default=current_text, placeholder=placeholder)


class SessionCompleter(_Completer):
    """Provide slash-command, workspace-file, and project-path completions."""

    def __init__(
        self,
        *,
        file_suggester: FileSuggester,
        workspace_root: Path | None,
        recent_projects: list[RecentProject],
    ) -> None:
        self.file_suggester = file_suggester
        self.workspace_root = workspace_root
        self.recent_projects = recent_projects

    _COMMAND_DESCRIPTIONS: dict[str, str] = {
        "/project": "Set the workspace directory",
        "/runs": "View recent workflow runs",
        "/new": "Start a fresh request draft",
        "/help": "Show commands and shortcuts",
        "/exit": "Quit FlowForge",
    }

    def get_completions(self, document, complete_event):  # type: ignore[no-untyped-def]
        """Yield prompt_toolkit completions for the current session input."""
        from prompt_toolkit.completion import Completion

        text_before_cursor = document.text_before_cursor
        stripped = text_before_cursor.lstrip()

        if stripped.startswith("/"):
            parts = stripped.split(maxsplit=1)
            if len(parts) == 1 and not stripped.endswith(" "):
                for command in SessionCommand:
                    if command.value.startswith(parts[0]):
                        desc = self._COMMAND_DESCRIPTIONS.get(command.value, "")
                        yield Completion(
                            command.value,
                            start_position=-len(parts[0]),
                            display=command.value,
                            display_meta=desc,
                        )
                return
            if parts[0] == SessionCommand.PROJECT.value:
                query = parts[1] if len(parts) > 1 else ""
                for candidate in self._project_candidates(query):
                    yield Completion(candidate, start_position=-len(query), display=candidate, display_meta="dir")
                return

        marker_index = text_before_cursor.rfind("@")
        if marker_index >= 0 and self.workspace_root is not None:
            query = text_before_cursor[marker_index + 1 :]
            for suggestion in self.file_suggester.suggest(workspace_root=self.workspace_root, query=query):
                yield Completion(
                    suggestion.value,
                    start_position=-len(query),
                    display=suggestion.display,
                    display_meta="file",
                )

    def _project_candidates(self, query: str) -> list[str]:
        """Return directory suggestions for the /project command."""
        candidates: list[str] = [entry.path for entry in self.recent_projects if query.lower() in entry.path.lower()]
        base = Path(query).expanduser() if query.strip() else Path.cwd()
        directory = base if base.is_dir() else base.parent
        if directory.exists():
            try:
                for path in sorted(directory.iterdir(), key=lambda item: item.name.lower()):
                    if not path.is_dir():
                        continue
                    candidate = str(path)
                    if query.lower() in candidate.lower():
                        candidates.append(candidate)
            except OSError:
                pass
        seen: set[str] = set()
        unique: list[str] = []
        for candidate in candidates:
            if candidate in seen:
                continue
            seen.add(candidate)
            unique.append(candidate)
        return unique[:8]

