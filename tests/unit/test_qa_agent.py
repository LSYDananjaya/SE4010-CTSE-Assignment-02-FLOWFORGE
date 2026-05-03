from __future__ import annotations

from flowforge.agents.qa_agent import QAAgent
from flowforge.models.outputs import ContextBundle, FileSnippet, IntakeResult, PlanResult, PlannedTask, QaResult
from flowforge.models.requests import UserRequest
from flowforge.models.state import WorkflowState
from flowforge.tools.qa_validator import QaValidatorTool
from flowforge.utils.errors import FlowForgeError


def test_qa_agent_flags_and_approves_complete_plan() -> None:
    # This happy path verifies that complete bug evidence reaches the QA prompt.
    request = UserRequest(
        title="Login timeout bug",
        description="Fix timeout and keep it local.",
        request_type="bug",
        constraints=["Local only"],
        reporter="qa",
        repo_path="C:/repo",
    )
    state = WorkflowState.initial(request=request)
    state.intake_result = IntakeResult(
        category="bug",
        severity="high",
        scope="backend",
        goals=["Fix timeout"],
        missing_information=[],
        summary="Fix timeout.",
    )
    state.context_bundle = ContextBundle(
        files_considered=1,
        selected_snippets=[
            FileSnippet(
                path="src/auth_service.py",
                language="python",
                reason="Relevant login path",
                content="def login(username: str, password: str) -> bool:\n    return True",
            )
        ],
        constraints=[],
        summary="Context found.",
    )
    state.plan_result = PlanResult(
        summary="Fix login timeout and test it.",
        tasks=[
            PlannedTask(
                task_id="T1",
                title="Fix timeout",
                description="Update timeout handling.",
                priority="high",
                dependencies=[],
                acceptance_criteria=["Login timeout handled gracefully"],
                risks=["Regression in auth flow"],
                owner="Student 4",
            )
        ],
        overall_risks=["Regression in auth flow"],
    )
    llm = __import__("tests.conftest", fromlist=["StubLLM"]).StubLLM(
        [
            {
                "approved": True,
                "findings": [],
                "rubric_checks": {
                    "four_agents": True,
                    "local_only": True,
                    "observability": True,
                    "tests_present": True,
                },
                "summary": "Plan is complete and compliant.",
            }
        ]
    )

    agent = QAAgent(llm_client=llm, tool=QaValidatorTool())
    updated = agent.run(state)

    assert isinstance(updated.qa_result, QaResult)
    assert updated.qa_result.approved is True
    assert updated.workflow_status == "qa_completed"
    assert "Request category: bug" in llm.calls[0]["prompt"]


def test_qa_agent_uses_feature_specific_rubric_language() -> None:
    # Feature requests should receive feature-oriented rubric wording in the LLM prompt.
    request = UserRequest(
        title="Category picker improvements",
        description="Suggest improvements for CategoryPicker.",
        request_type="feature",
        constraints=["Local only"],
        reporter="pm",
        repo_path="C:/repo",
    )
    state = WorkflowState.initial(request=request)
    state.intake_result = IntakeResult(
        category="feature",
        severity="medium",
        scope="frontend",
        goals=["Improve CategoryPicker UX"],
        missing_information=[],
        summary="Improve CategoryPicker UX.",
    )
    state.context_bundle = ContextBundle(
        files_considered=1,
        selected_snippets=[
            FileSnippet(
                path="src/components/CategoryPicker.tsx",
                language="tsx",
                reason="Attached UI component",
                content="export function CategoryPicker() { return null; }",
            )
        ],
        constraints=[],
        summary="Component found.",
    )
    state.plan_result = PlanResult(
        summary="Add search and accessibility improvements.",
        tasks=[
            PlannedTask(
                task_id="T1",
                title="Refine component UX",
                description="Improve accessibility and discoverability.",
                priority="medium",
                dependencies=[],
                acceptance_criteria=["Users can filter categories quickly"],
                risks=["UI regression"],
                owner="Student 4",
            )
        ],
        overall_risks=["UI regression"],
    )
    llm = __import__("tests.conftest", fromlist=["StubLLM"]).StubLLM(
        [
            {
                "approved": True,
                "findings": [],
                "rubric_checks": {
                    "feature_scope": True,
                    "ux_impact": True,
                    "observability": True,
                    "tests_present": True,
                },
                "summary": "Feature plan is complete.",
            }
        ]
    )

    updated = QAAgent(llm_client=llm, tool=QaValidatorTool()).run(state)

    assert updated.qa_result is not None
    assert updated.qa_result.approved is True
    assert "Request category: feature" in llm.calls[0]["prompt"]
    assert "Expected QA emphasis: requirements coverage, UX/API impact" in llm.calls[0]["prompt"]


def test_qa_validator_flags_missing_local_only_and_observability_evidence() -> None:
    # Missing policy evidence should remain visible before the LLM review stage.
    findings = QaValidatorTool().run(
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
                    reason="Export entrypoint",
                    content="def export_tasks(format_name: str) -> str:\n    return format_name",
                )
            ],
            constraints=[],
            summary="Context found without deployment or audit details.",
        ),
        plan=PlanResult(
            summary="Implement CSV export with UX improvements.",
            tasks=[
                PlannedTask(
                    task_id="T1",
                    title="Implement export logic",
                    description="Add CSV export support.",
                    priority="high",
                    dependencies=[],
                    acceptance_criteria=["CSV export returns the expected file content"],
                    risks=["Formatting mismatch"],
                    owner="Student 4",
                )
            ],
            overall_risks=["Formatting mismatch"],
        ),
    )

    assert any("local-only" in finding.lower() for finding in findings)
    assert any("observability" in finding.lower() for finding in findings)


def test_qa_validator_accepts_natural_local_constraint_language() -> None:
    # Natural language constraints should satisfy local-only checks when intent is clear.
    findings = QaValidatorTool().run(
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
                    reason="Export entrypoint",
                    content="def export_tasks() -> str:\n    return 'csv'",
                )
            ],
            constraints=[],
            summary="Trace logging is enabled for the workflow.",
        ),
        plan=PlanResult(
            summary="Implement CSV export with requirements coverage and logging.",
            tasks=[
                PlannedTask(
                    task_id="T1",
                    title="Implement CSV export",
                    description="Add export support and validate the API requirement.",
                    priority="high",
                    dependencies=[],
                    acceptance_criteria=["CSV export works"],
                    risks=["Formatting mismatch"],
                    owner="Student 4",
                )
            ],
            overall_risks=["Formatting mismatch"],
        ),
        workflow_constraints=["Keep outputs local", "Prefer incremental changes"],
        observability_enabled=False,
    )

    assert not any("local-only" in finding.lower() for finding in findings)


def test_qa_agent_falls_back_to_deterministic_result_when_llm_output_is_invalid() -> None:
    request = UserRequest(
        title="CSV export feature",
        description="Add CSV export with local-only constraints.",
        request_type="feature",
        constraints=["Local only"],
        reporter="pm",
        repo_path="C:/repo",
    )
    state = WorkflowState.initial(request=request)
    state.intake_result = IntakeResult(
        category="feature",
        severity="medium",
        scope="backend",
        goals=["Add CSV export"],
        missing_information=[],
        summary="Add CSV export.",
    )
    state.context_bundle = ContextBundle(
        files_considered=1,
        selected_snippets=[
            FileSnippet(
                path="src/export_tasks.py",
                language="python",
                reason="Export entrypoint",
                content="def export_tasks() -> str:\n    return 'csv'",
            )
        ],
        constraints=["Local only"],
        summary="Trace logging is already enabled for the workflow.",
    )
    state.plan_result = PlanResult(
        summary="Implement CSV export with requirements coverage, API validation, and trace logging.",
        tasks=[
            PlannedTask(
                task_id="T1",
                title="Implement CSV export",
                description="Add export support, document API behavior, and validate the main requirement locally.",
                priority="high",
                dependencies=[],
                acceptance_criteria=["CSV export works locally"],
                risks=["Formatting mismatch"],
                owner="Student 4",
            )
        ],
        overall_risks=["Formatting mismatch"],
    )

    class InvalidQaLlm:
        def generate_structured(self, **kwargs):  # type: ignore[no-untyped-def]
            raise FlowForgeError("Ollama structured generation failed. metadata={'agent': 'qa'} raw_preview=invalid")

    updated = QAAgent(llm_client=InvalidQaLlm(), tool=QaValidatorTool()).run(state)

    assert updated.qa_result is not None
    assert updated.qa_result.approved is True
    assert updated.trace_context["qa"]["fallback_used"] is True


def test_qa_agent_filters_plan_risks_out_of_llm_findings() -> None:
    request = UserRequest(
        title="Login timeout bug",
        description="Fix the login timeout while keeping the API stable.",
        request_type="bug",
        constraints=["Local only"],
        reporter="qa",
        repo_path="C:/repo",
    )
    state = WorkflowState.initial(request=request)
    state.intake_result = IntakeResult(
        category="bug",
        severity="high",
        scope="backend",
        goals=["Fix timeout"],
        missing_information=[],
        summary="Fix timeout.",
    )
    state.context_bundle = ContextBundle(
        files_considered=1,
        selected_snippets=[
            FileSnippet(
                path="src/auth_service.py",
                language="python",
                reason="Relevant login path",
                content="def login(username: str, password: str) -> bool:\n    return True",
            )
        ],
        constraints=["Local only"],
        summary="Trace logging is enabled for the workflow.",
    )
    state.plan_result = PlanResult(
        summary="Implement the fix with validation and trace logging.",
        tasks=[
            PlannedTask(
                task_id="T1",
                title="Fix timeout",
                description="Update the timeout handling and validate the fix.",
                priority="high",
                dependencies=[],
                acceptance_criteria=["Timeout fix works locally"],
                risks=["The fix may introduce authentication regressions if request handling changes."],
                owner="Student 4",
            )
        ],
        overall_risks=["The fix may introduce authentication regressions if request handling changes."],
    )
    llm = __import__("tests.conftest", fromlist=["StubLLM"]).StubLLM(
        [
            {
                "approved": False,
                "findings": ["The fix may introduce authentication regressions if request handling changes."],
                "rubric_checks": {
                    "local_only": True,
                    "observability": True,
                    "tests_present": True,
                },
                "summary": "Needs review.",
            }
        ]
    )

    updated = QAAgent(llm_client=llm, tool=QaValidatorTool()).run(state)

    assert updated.qa_result is not None
    assert updated.qa_result.findings == []
    assert updated.qa_result.approved is True
