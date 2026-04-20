from __future__ import annotations

from flowforge.models.outputs import IntakeResult


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
