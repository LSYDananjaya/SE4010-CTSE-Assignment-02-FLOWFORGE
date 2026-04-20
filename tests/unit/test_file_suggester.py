from __future__ import annotations

from flowforge.launcher.file_suggester import FileSuggester


def test_fuzzy_file_matching_within_workspace(sample_repo) -> None:
    suggester = FileSuggester()

    suggestions = suggester.suggest(workspace_root=sample_repo, query="auth")

    assert suggestions
    assert suggestions[0].value.endswith("auth_service.py")


def test_arrow_selection_state_transitions() -> None:
    suggester = FileSuggester()
    items = [
        ("src/auth_service.py", "src/auth_service.py"),
        ("src/export_tasks.py", "src/export_tasks.py"),
    ]

    index = suggester.move_selection(current_index=0, direction="down", total=len(items))
    assert index == 1
    index = suggester.move_selection(current_index=1, direction="down", total=len(items))
    assert index == 0
    index = suggester.move_selection(current_index=0, direction="up", total=len(items))
    assert index == 1
