from __future__ import annotations

from flowforge.tools.repo_context_finder import RepoContextFinderTool


def test_context_eval_limits_selected_content(sample_repo) -> None:
    # Evaluation goal: keep retrieved evidence bounded so the local SLM receives
    # concise context instead of an oversized repository dump.
    tool = RepoContextFinderTool(max_files=2, snippet_chars=80)
    result = tool.run(
        repo_path=sample_repo,
        query="login timeout auth",
        constraints=["Local only"],
    )

    assert len(result.candidates) <= 2
    assert all(len(candidate.content) <= 80 for candidate in result.candidates)


def test_context_eval_blocks_attachment_escape_attempt(sample_repo) -> None:
    # Security goal: user-supplied attachments must not read files outside the
    # selected repository root.
    result = RepoContextFinderTool().run(
        repo_path=sample_repo,
        query="inspect system secrets",
        constraints=["Local only"],
        attachments=["../../outside.txt"],
    )

    assert result.missing_attachments == ["../../outside.txt"]
