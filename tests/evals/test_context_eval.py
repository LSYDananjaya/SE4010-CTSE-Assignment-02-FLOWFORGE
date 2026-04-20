from __future__ import annotations

from flowforge.tools.repo_context_finder import RepoContextFinderTool


def test_context_eval_limits_selected_content(sample_repo) -> None:
    tool = RepoContextFinderTool(max_files=2, snippet_chars=80)
    result = tool.run(
        repo_path=sample_repo,
        query="login timeout auth",
        constraints=["Local only"],
    )

    assert len(result.candidates) <= 2
    assert all(len(candidate.content) <= 80 for candidate in result.candidates)
