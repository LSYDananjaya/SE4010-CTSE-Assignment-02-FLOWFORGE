from __future__ import annotations

from flowforge.models.outputs import ContextBundle, FileSnippet, IntakeResult, PlanResult, PlannedTask
from flowforge.tools.qa_validator import QaValidatorTool


def test_qa_eval_flags_missing_acceptance_criteria() -> None:
    # Eval coverage keeps acceptance criteria as a non-negotiable QA signal.
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


def test_qa_eval_flags_missing_observability_and_local_only_controls() -> None:
    # Eval coverage pairs observability and local-only controls because both are workflow gates.
    tool = QaValidatorTool()
    findings = tool.run(
        intake=IntakeResult(
            category="feature",
            severity="medium",
            scope="backend",
            goals=["Add CSV export"],
            missing_information=[],
            summary="Add CSV export.",
        ),
        context=ContextBundle(
            files_considered=1,
            selected_snippets=[
                FileSnippet(
                    path="src/export_tasks.py",
                    language="python",
                    reason="Relevant export code",
                    content="def export_tasks() -> str:\n    return 'csv'",
                )
            ],
            constraints=[],
            summary="Context found.",
        ),
        plan=PlanResult(
            summary="Implement CSV export with accessibility improvements.",
            tasks=[
                PlannedTask(
                    task_id="T1",
                    title="Implement CSV export",
                    description="Add export support with validation.",
                    priority="high",
                    dependencies=[],
                    acceptance_criteria=["CSV export works locally"],
                    risks=["Formatting mismatch"],
                    owner="Student 4",
                )
            ],
            overall_risks=["Formatting mismatch"],
        ),
    )

    assert any("observability" in finding.lower() for finding in findings)
    assert any("local-only" in finding.lower() for finding in findings)
