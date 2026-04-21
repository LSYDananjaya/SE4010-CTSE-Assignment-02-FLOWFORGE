from __future__ import annotations

from flowforge.models.outputs import IntakeResult
from flowforge.models.requests import UserRequest
from flowforge.tools.intake_parser import IntakeParserTool
from flowforge.utils.errors import ToolExecutionError


def test_intake_eval_requires_core_fields() -> None:
    result = IntakeResult(
        category="bug",
        severity="medium",
        scope="backend",
        goals=["Fix timeout"],
        missing_information=[],
        summary="Fix timeout in login flow.",
    )

    assert result.category
    assert result.severity
    assert result.scope
    assert len(result.goals) >= 1


def test_intake_eval_rejects_blank_request_payload() -> None:
    request = UserRequest(
        title="Investigate timeout",
        description="          ",
        request_type="bug",
        constraints=[" ", "Local only"],
        reporter="qa",
        repo_path="C:/repo",
    )

    with __import__("pytest").raises(ToolExecutionError):
        IntakeParserTool().run(request)
