from __future__ import annotations

from flowforge.launcher.file_suggester import FileSuggester


def test_fuzzy_file_matching_within_workspace(sample_repo) -> None:
    suggester = FileSuggester()

    suggestions = suggester.suggest(workspace_root=sample_repo, query="auth")

    assert suggestions.candidates
    assert suggestions.candidates[0].value.endswith("auth_service.py")
    assert suggestions.total_count >= 1


def test_suggester_reports_total_count_before_visible_slice(sample_repo) -> None:
    suggester = FileSuggester()

    all_matches = suggester.suggest(workspace_root=sample_repo, query="", limit=None)
    visible_matches = suggester.suggest(workspace_root=sample_repo, query="", limit=2)

    assert all_matches.total_count >= 3
    assert len(visible_matches.candidates) == 2
    assert visible_matches.total_count == all_matches.total_count


def test_suggester_keeps_sorted_visible_candidates(sample_repo) -> None:
    suggester = FileSuggester()

    result = suggester.suggest(workspace_root=sample_repo, query="src", limit=5)

    assert [candidate.value for candidate in result.candidates] == sorted(
        [candidate.value for candidate in result.candidates]
    )


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
