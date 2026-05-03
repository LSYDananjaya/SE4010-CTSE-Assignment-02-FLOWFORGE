from __future__ import annotations

from flowforge.agents.planning_agent import PlanningAgent
from flowforge.models.outputs import ContextBundle, FileSnippet, IntakeResult, PlanResult, PlannedTask
from flowforge.models.requests import UserRequest
from flowforge.models.state import WorkflowState
from flowforge.tools.task_plan_builder import TaskPlanBuilderTool
from flowforge.utils.errors import FlowForgeError
from flowforge.utils.errors import ToolExecutionError


def test_planning_agent_creates_dependency_aware_plan() -> None:
    request = UserRequest(
        title="Export tasks feature",
        description="Add CSV task export.",
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
        files_considered=2,
        selected_snippets=[
            FileSnippet(
                path="src/export_tasks.py",
                language="python",
                reason="Existing export entrypoint",
                content="def export_tasks(format_name: str) -> str:\n    return f'exported:{format_name}'",
            )
        ],
        constraints=["Keep API simple"],
        summary="Export module found.",
    )
    llm = __import__("tests.conftest", fromlist=["StubLLM"]).StubLLM(
        [
            {
                "summary": "Implement CSV export with tests.",
                "tasks": [
                    {
                        "task_id": "T1",
                        "title": "Update export module",
                        "description": "Add CSV generation.",
                        "priority": "high",
                        "dependencies": [],
                        "acceptance_criteria": ["CSV output can be generated"],
                        "risks": ["Formatting mismatch"],
                        "owner": "Student 3",
                    },
                    {
                        "task_id": "T2",
                        "title": "Add tests",
                        "description": "Cover CSV export path.",
                        "priority": "medium",
                        "dependencies": ["T1"],
                        "acceptance_criteria": ["Regression tests pass"],
                        "risks": ["Missing edge cases"],
                        "owner": "Student 3",
                    },
                ],
                "overall_risks": ["CSV escaping"],
            }
        ]
    )

    agent = PlanningAgent(llm_client=llm, tool=TaskPlanBuilderTool())
    updated = agent.run(state)

    assert isinstance(updated.plan_result, PlanResult)
    assert [task.task_id for task in updated.plan_result.tasks] == ["T1", "T2"]
    assert updated.plan_result.tasks[1].dependencies == ["T1"]
    assert updated.workflow_status == "planning_completed"
    assert "Request category: feature" in llm.calls[0]["prompt"]


def test_planning_agent_includes_bug_specific_prompt_context() -> None:
    request = UserRequest(
        title="Login timeout bug",
        description="Fix login timeout.",
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
        goals=["Reproduce timeout", "Fix timeout"],
        missing_information=[],
        summary="Fix login timeout.",
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
        summary="Auth context found.",
    )
    llm = __import__("tests.conftest", fromlist=["StubLLM"]).StubLLM(
        [
            {
                "summary": "Investigate, fix, and validate the timeout defect.",
                "tasks": [
                    {
                        "task_id": "T1",
                        "title": "Reproduce timeout",
                        "description": "Confirm the failure path before changing code.",
                        "priority": "high",
                        "dependencies": [],
                        "acceptance_criteria": ["A deterministic repro exists"],
                        "risks": ["Environment-specific timing"],
                        "owner": "Student 3",
                    }
                ],
                "overall_risks": ["Regression in login flow"],
            }
        ]
    )

    updated = PlanningAgent(llm_client=llm, tool=TaskPlanBuilderTool()).run(state)

    assert updated.plan_result is not None
    assert updated.plan_result.tasks[0].title == "Reproduce timeout"
    assert "Request category: bug" in llm.calls[0]["prompt"]
    assert "Expected planning emphasis: reproduction, root cause" in llm.calls[0]["prompt"]


def test_task_plan_builder_rejects_dependency_cycles() -> None:
    tool = TaskPlanBuilderTool()
    cyclic_plan = PlanResult(
        summary="Plan with a cycle.",
        tasks=[
            PlannedTask(
                task_id="T1",
                title="First",
                description="First task",
                priority="high",
                dependencies=["T2"],
                acceptance_criteria=["T1 done"],
                risks=["Regression"],
                owner="Student 3",
            ),
            PlannedTask(
                task_id="T2",
                title="Second",
                description="Second task",
                priority="medium",
                dependencies=["T1"],
                acceptance_criteria=["T2 done"],
                risks=["Order issue"],
                owner="Student 3",
            ),
        ],
        overall_risks=["Dependency cycle"],
    )

    with __import__("pytest").raises(ToolExecutionError, match="dependency cycle"):
        tool.run(cyclic_plan)


def test_task_plan_builder_backfills_missing_risks() -> None:
    tool = TaskPlanBuilderTool()
    plan = PlanResult(
        summary="Plan without explicit risks.",
        tasks=[
            PlannedTask(
                task_id="T1",
                title="Implement export",
                description="Add CSV export.",
                priority="high",
                dependencies=[],
                acceptance_criteria=["CSV export works"],
                risks=[],
                owner="Student 3",
            )
        ],
        overall_risks=[],
    )

    normalized = tool.run(plan)

    assert normalized.tasks[0].risks
    assert normalized.overall_risks


def test_planning_agent_falls_back_to_deterministic_plan_when_llm_output_is_invalid() -> None:
    request = UserRequest(
        title="Login timeout bug",
        description="Fix login timeout without changing the public API.",
        request_type="bug",
        constraints=["Local only", "Preserve login API"],
        reporter="qa",
        repo_path="C:/repo",
    )
    state = WorkflowState.initial(request=request)
    state.intake_result = IntakeResult(
        category="bug",
        severity="high",
        scope="backend",
        goals=["Reproduce the timeout", "Fix the timeout", "Prevent regression"],
        missing_information=[],
        summary="Fix login timeout.",
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
        summary="Auth context found.",
    )

    class InvalidPlanningLlm:
        def generate_structured(self, **kwargs):  # type: ignore[no-untyped-def]
            raise FlowForgeError("Ollama structured generation failed. metadata={'agent': 'planning'} raw_preview=invalid")

    updated = PlanningAgent(llm_client=InvalidPlanningLlm(), tool=TaskPlanBuilderTool()).run(state)

    assert updated.plan_result is not None
    assert updated.plan_result.tasks
    assert updated.trace_context["planning"]["fallback_used"] is True
    assert any("repro" in task.title.lower() or "validate" in task.title.lower() for task in updated.plan_result.tasks)
