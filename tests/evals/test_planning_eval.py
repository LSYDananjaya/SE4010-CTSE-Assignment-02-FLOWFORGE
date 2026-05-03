from __future__ import annotations

from flowforge.models.outputs import PlanResult, PlannedTask
from flowforge.tools.task_plan_builder import TaskPlanBuilderTool


def test_planning_eval_rejects_invalid_dependencies() -> None:
    tool = TaskPlanBuilderTool()
    plan = PlanResult(
        summary="Plan",
        tasks=[
            PlannedTask(
                task_id="T1",
                title="First",
                description="First step",
                priority="high",
                dependencies=[],
                acceptance_criteria=["Works"],
                risks=["Risk"],
                owner="Student 3",
            ),
            PlannedTask(
                task_id="T2",
                title="Second",
                description="Second step",
                priority="medium",
                dependencies=["T1"],
                acceptance_criteria=["Still works"],
                risks=["Another risk"],
                owner="Student 3",
            ),
        ],
        overall_risks=["Risk"],
    )

    normalized = tool.run(plan)
    task_ids = {task.task_id for task in normalized.tasks}
    assert all(dep in task_ids for task in normalized.tasks for dep in task.dependencies)
    assert all(task.task_id not in task.dependencies for task in normalized.tasks)


def test_planning_eval_rejects_dependency_cycles() -> None:
    tool = TaskPlanBuilderTool()
    plan = PlanResult(
        summary="Plan",
        tasks=[
            PlannedTask(
                task_id="T1",
                title="First",
                description="First step",
                priority="high",
                dependencies=["T2"],
                acceptance_criteria=["Works"],
                risks=["Risk"],
                owner="Student 3",
            ),
            PlannedTask(
                task_id="T2",
                title="Second",
                description="Second step",
                priority="medium",
                dependencies=["T1"],
                acceptance_criteria=["Still works"],
                risks=["Another risk"],
                owner="Student 3",
            ),
        ],
        overall_risks=["Risk"],
    )

    with __import__("pytest").raises(__import__("flowforge.utils.errors", fromlist=["ToolExecutionError"]).ToolExecutionError):
        tool.run(plan)


def test_planning_eval_backfills_missing_risk_metadata() -> None:
    tool = TaskPlanBuilderTool()
    plan = PlanResult(
        summary="Plan",
        tasks=[
            PlannedTask(
                task_id="T1",
                title="Implement export",
                description="Add export support",
                priority="high",
                dependencies=[],
                acceptance_criteria=["Export works"],
                risks=[],
                owner="Student 3",
            )
        ],
        overall_risks=[],
    )

    normalized = tool.run(plan)

    assert normalized.tasks[0].risks
    assert normalized.overall_risks
