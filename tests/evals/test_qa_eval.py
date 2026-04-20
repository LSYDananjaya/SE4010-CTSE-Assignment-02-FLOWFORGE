from __future__ import annotations

from flowforge.models.outputs import ContextBundle, FileSnippet, IntakeResult, PlanResult, PlannedTask
from flowforge.tools.qa_validator import QaValidatorTool


def test_qa_eval_flags_missing_acceptance_criteria() -> None:
    tool = QaValidatorTool()
    findings = tool.run(
        intake=IntakeResult(
            category="bug",
            severity="high",
            scope="backend",
            goals=["Fix timeout"],
            missing_information=[],
            summary="Fix timeout.",
        ),
        context=ContextBundle(
            files_considered=1,
            selected_snippets=[
                FileSnippet(
                    path="src/auth_service.py",
                    language="python",
                    reason="Relevant auth code",
                    content="def login() -> None:\n    pass",
                )
            ],
            constraints=[],
            summary="Context found.",
        ),
        plan=PlanResult(
            summary="Plan",
            tasks=[
                PlannedTask(
                    task_id="T1",
                    title="Task",
                    description="Desc",
                    priority="high",
                    dependencies=[],
                    acceptance_criteria=[],
                    risks=["Regression"],
                    owner="Student 4",
                )
            ],
            overall_risks=["Regression"],
        ),
    )

    assert any("acceptance criteria" in finding.lower() for finding in findings)
