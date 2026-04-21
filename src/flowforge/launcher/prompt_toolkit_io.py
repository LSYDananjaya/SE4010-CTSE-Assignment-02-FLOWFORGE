from __future__ import annotations

from pathlib import Path

from flowforge.launcher.input_controller import LauncherInputController

try:
    from prompt_toolkit.completion import Completer as _Completer
except ModuleNotFoundError:  # pragma: no cover
    _Completer = object  # type: ignore[misc,assignment]

from flowforge.launcher.file_suggester import FileSuggester
from flowforge.launcher.models import PromptSuggestionState, RecentProject, SessionCommand, SuggestionCandidate


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
        self.input_controller = LauncherInputController()
        self.suggestion_controller = PromptSuggestionController(file_suggester=self.file_suggester)

    def read_input(
        self,
        *,
        placeholder: str,
        workspace_root: Path | None = None,
        current_text: str = "",
        recent_projects: list[RecentProject] | None = None,
    ) -> str:
        """Read a single session prompt with inline completions and shortcuts."""
        from prompt_toolkit.application import Application
        from prompt_toolkit.buffer import Buffer
        from prompt_toolkit.filters import Condition
        from prompt_toolkit.key_binding import KeyBindings
        from prompt_toolkit.layout import ConditionalContainer, HSplit, Layout, Window
        from prompt_toolkit.layout.controls import BufferControl, FormattedTextControl
        from prompt_toolkit.layout.dimension import Dimension
        from prompt_toolkit.layout.processors import BeforeInput, ConditionalProcessor
        from prompt_toolkit.styles import Style
        from prompt_toolkit.widgets import Box, Frame

        completer = SessionCompleter(
            file_suggester=self.file_suggester,
            workspace_root=workspace_root,
            recent_projects=recent_projects or [],
        )
        suggestion_state = self.suggestion_controller.build_state(
            text=current_text,
            cursor_position=len(current_text),
            workspace_root=workspace_root,
        )
        result: dict[str, str] = {"text": current_text}

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

        @bindings.add("down")
        def _down(event) -> None:  # type: ignore[no-untyped-def]
            nonlocal suggestion_state
            if suggestion_state.active and suggestion_state.total_count > 0:
                suggestion_state = self.suggestion_controller.move_selection(suggestion_state, "down")
                event.app.invalidate()
                return
            event.current_buffer.auto_down()

        @bindings.add("up")
        def _up(event) -> None:  # type: ignore[no-untyped-def]
            nonlocal suggestion_state
            if suggestion_state.active and suggestion_state.total_count > 0:
                suggestion_state = self.suggestion_controller.move_selection(suggestion_state, "up")
                event.app.invalidate()
                return
            event.current_buffer.auto_up()

        @bindings.add("tab")
        def _tab(event) -> None:  # type: ignore[no-untyped-def]
            nonlocal suggestion_state
            if suggestion_state.active and suggestion_state.total_count > 0:
                candidate = suggestion_state.candidates[suggestion_state.selected_index]
                updated_text, updated_cursor = self.suggestion_controller.apply_candidate(
                    text=event.app.current_buffer.text,
                    cursor_position=event.app.current_buffer.cursor_position,
                    candidate=candidate,
                    mode=suggestion_state.mode,
                )
                event.app.current_buffer.text = updated_text
                event.app.current_buffer.cursor_position = updated_cursor
                suggestion_state = self.suggestion_controller.build_state(
                    text=updated_text,
                    cursor_position=updated_cursor,
                    workspace_root=workspace_root,
                )
                event.app.invalidate()
                return
            if event.current_buffer.complete_state is not None and event.current_buffer.complete_state.current_completion is not None:
                event.current_buffer.apply_completion(event.current_buffer.complete_state.current_completion)
                return
            event.current_buffer.start_completion(select_first=True)

        @bindings.add("enter")
        def _enter(event) -> None:  # type: ignore[no-untyped-def]
            nonlocal suggestion_state
            if suggestion_state.active and suggestion_state.total_count > 0:
                candidate = suggestion_state.candidates[suggestion_state.selected_index]
                if self.suggestion_controller.should_submit_on_enter(suggestion_state):
                    result["text"] = self.suggestion_controller.submit_candidate(candidate, mode=suggestion_state.mode)
                    event.app.exit(result=result["text"])
                    return
                updated_text, updated_cursor = self.suggestion_controller.apply_candidate(
                    text=event.app.current_buffer.text,
                    cursor_position=event.app.current_buffer.cursor_position,
                    candidate=candidate,
                    mode=suggestion_state.mode,
                )
                event.app.current_buffer.text = updated_text
                event.app.current_buffer.cursor_position = updated_cursor
                suggestion_state = self.suggestion_controller.build_state(
                    text=updated_text,
                    cursor_position=updated_cursor,
                    workspace_root=workspace_root,
                )
                event.app.invalidate()
                return
            result["text"] = event.app.current_buffer.text
            event.app.exit(result=result["text"])

        def _footer_toolbar() -> list[tuple[str, str]]:
            return [
                ("class:footer.bg", " "),
                ("class:footer.cmd", " /project"),
                ("class:footer.sep", " │ "),
                ("class:footer.cmd", "/runs"),
                ("class:footer.sep", " │ "),
                ("class:footer.cmd", "/new"),
                ("class:footer.sep", " │ "),
                ("class:footer.cmd", "/help"),
                ("class:footer.sep", " │ "),
                ("class:footer.cmd", "/exit"),
                ("class:footer.sep", "   ·   "),
                ("class:footer.key", "Tab "),
                ("class:footer.hint", "accept  "),
                ("class:footer.key", "Ctrl+P "),
                ("class:footer.hint", "project  "),
                ("class:footer.key", "Ctrl+F "),
                ("class:footer.hint", "attach"),
            ]

        pt_style = Style.from_dict({
            "": "#9ca3af bg:#0b0b0b",
            "frame.border": "#60a5fa",
            "input-field": "bg:#0b0b0b #e5e7eb",
            "input-prefix": "bold #c084fc",
            "input-text": "#e5e7eb",
            "input-placeholder": "italic #6b7280",
            "suggestion.default": "#6b7280",
            "suggestion.selected": "bold #d8b4fe",
            "suggestion.count": "#9ca3af",
            "footer.bg": "bg:#0b0b0b",
            "footer.cmd": "#94a3b8",
            "footer.sep": "#374151",
            "footer.key": "bold #cbd5e1",
            "footer.hint": "#6b7280",
        })

        buffer = Buffer(completer=completer, complete_while_typing=True)
        buffer.text = current_text
        buffer.cursor_position = len(current_text)

        def _refresh_state(_=None) -> None:
            nonlocal suggestion_state
            suggestion_state = self.suggestion_controller.build_state(
                text=buffer.text,
                cursor_position=buffer.cursor_position,
                workspace_root=workspace_root,
            )

        buffer.on_text_changed += _refresh_state
        buffer.on_cursor_position_changed += _refresh_state

        def _suggestion_lines():
            fragments: list[tuple[str, str]] = []
            visible = self.suggestion_controller.visible_candidates(suggestion_state)
            for index, candidate in enumerate(visible):
                absolute_index = suggestion_state.scroll_offset + index
                style = "class:suggestion.selected" if absolute_index == suggestion_state.selected_index else "class:suggestion.default"
                prefix = "▸ " if absolute_index == suggestion_state.selected_index else "  "
                line = f"{prefix}{candidate.display}"
                if candidate.meta:
                    line = f"{line}  {candidate.meta}"
                fragments.append((style, f"{line}\n"))
            pager = self.suggestion_controller.pager_text(suggestion_state)
            if pager:
                fragments.append(("class:suggestion.count", f"▾\n{pager}"))
            return fragments

        suggestion_control = FormattedTextControl(_suggestion_lines, focusable=False)

        input_window = Window(
            BufferControl(
                buffer=buffer,
                input_processors=[
                    ConditionalProcessor(
                        processor=BeforeInput([("class:input-prefix", "❯ ")]),
                        filter=Condition(lambda: True),
                    )
                ],
            ),
            height=1,
            style="class:input-field",
        )

        container = HSplit(
            [
                Frame(Box(input_window, padding=0), style="class:frame.border"),
                ConditionalContainer(
                    Window(
                        suggestion_control,
                        height=Dimension(preferred=self.suggestion_controller.window_height),
                        dont_extend_height=True,
                    ),
                    filter=Condition(lambda: suggestion_state.active and suggestion_state.total_count > 0),
                ),
                Window(
                    FormattedTextControl(_footer_toolbar),
                    height=1,
                    style="class:footer.bg",
                    dont_extend_height=True,
                ),
            ]
        )
        app = Application(
            layout=Layout(container),
            key_bindings=bindings,
            style=pt_style,
            full_screen=False,
            mouse_support=False,
        )
        _refresh_state()
        return app.run()


class PromptSuggestionController:
    """Build and navigate screenshot-style @ suggestion state."""

    _COMMAND_DESCRIPTIONS: dict[str, str] = {
        "/project": "Set workspace directory",
        "/runs": "View recent runs",
        "/new": "Start fresh draft",
        "/help": "Show commands",
        "/exit": "Quit FlowForge",
    }

    def __init__(self, *, file_suggester: FileSuggester | None = None, visible_limit: int = 7) -> None:
        self.file_suggester = file_suggester or FileSuggester()
        self.visible_limit = visible_limit
        self.window_height = visible_limit + 2

    def build_state(self, *, text: str, cursor_position: int, workspace_root: Path | None) -> PromptSuggestionState:
        """Return active suggestion state for the current cursor location."""
        before_cursor = text[:cursor_position]
        slash_state = self._build_command_state(before_cursor)
        if slash_state.active:
            return slash_state

        if workspace_root is None:
            return PromptSuggestionState()
        marker_index = before_cursor.rfind("@")
        if marker_index < 0:
            return PromptSuggestionState()
        query = before_cursor[marker_index + 1 :]
        if any(char.isspace() for char in query):
            return PromptSuggestionState()
        results = self.file_suggester.suggest(workspace_root=workspace_root, query=query, limit=None)
        return PromptSuggestionState(
            active=True,
            mode="file",
            query=query,
            candidates=results.candidates,
            total_count=results.total_count,
            selected_index=0,
            scroll_offset=0,
        )

    def _build_command_state(self, before_cursor: str) -> PromptSuggestionState:
        stripped = before_cursor.lstrip()
        if not stripped.startswith("/"):
            return PromptSuggestionState()
        if " " in stripped:
            command_prefix = stripped.split(maxsplit=1)[0]
            if command_prefix != SessionCommand.PROJECT.value:
                return PromptSuggestionState()
        query = stripped if " " not in stripped else ""
        if not query:
            return PromptSuggestionState()
        candidates = [
            SuggestionCandidate(display=command.value, value=command.value, meta=self._COMMAND_DESCRIPTIONS.get(command.value, ""))
            for command in SessionCommand
            if command.value.startswith(query)
        ]
        return PromptSuggestionState(
            active=bool(candidates),
            mode="command" if candidates else "none",
            query=query,
            candidates=candidates,
            total_count=len(candidates),
            selected_index=0,
            scroll_offset=0,
        )

    def move_selection(self, state: PromptSuggestionState, direction: str) -> PromptSuggestionState:
        """Wrap selection movement and keep the visible window aligned."""
        if not state.active or state.total_count <= 0:
            return state
        selected_index = self.file_suggester.move_selection(
            current_index=state.selected_index,
            direction=direction,
            total=state.total_count,
        )
        scroll_offset = state.scroll_offset
        if selected_index < scroll_offset:
            scroll_offset = selected_index
        elif selected_index >= scroll_offset + self.visible_limit:
            scroll_offset = selected_index - self.visible_limit + 1
        return state.model_copy(update={"selected_index": selected_index, "scroll_offset": max(scroll_offset, 0)})

    def visible_candidates(self, state: PromptSuggestionState) -> list[SuggestionCandidate]:
        """Return the visible candidate slice for the current scroll position."""
        if not state.active:
            return []
        return state.candidates[state.scroll_offset : state.scroll_offset + self.visible_limit]

    def apply_candidate(
        self,
        *,
        text: str,
        cursor_position: int,
        candidate: SuggestionCandidate,
        mode: str,
    ) -> tuple[str, int]:
        """Apply a selected candidate to the active text buffer."""
        if mode == "command":
            return candidate.value, len(candidate.value)
        controller = LauncherInputController()
        updated = controller.apply_suggestion(
            controller.parse_session_input(text, cursor_position=cursor_position),
            candidate,
            finalize=True,
        )
        return updated.raw_text, updated.cursor_position

    @staticmethod
    def should_submit_on_enter(state: PromptSuggestionState) -> bool:
        """Return whether Enter should submit immediately for the active picker."""
        return state.active and state.mode == "command" and state.total_count > 0

    @staticmethod
    def submit_candidate(candidate: SuggestionCandidate, *, mode: str) -> str:
        """Return the submitted value for a selected suggestion."""
        if mode == "command":
            return candidate.value
        return candidate.display

    @staticmethod
    def pager_text(state: PromptSuggestionState) -> str:
        """Return screenshot-style `(selected/total)` pager text."""
        if not state.active or state.total_count <= 0:
            return ""
        return f"({state.selected_index + 1}/{state.total_count})"


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
