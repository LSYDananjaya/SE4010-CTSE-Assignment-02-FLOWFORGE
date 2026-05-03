from __future__ import annotations

from flowforge.models.outputs import PlanResult
from flowforge.utils.errors import ToolExecutionError


class TaskPlanBuilderTool:
    """Normalize plan ordering and validate dependency integrity."""

    def run(self, plan: PlanResult) -> PlanResult:
        """Validate references, normalize task order, and remove duplicate dependencies."""
        task_ids = {task.task_id for task in plan.tasks}
        for task in plan.tasks:
            if task.task_id in task.dependencies:
                raise ToolExecutionError(f"Task {task.task_id} cannot depend on itself.")
            missing = [dependency for dependency in task.dependencies if dependency not in task_ids]
            if missing:
                raise ToolExecutionError(f"Task {task.task_id} references unknown dependencies: {missing}")
            task.dependencies = list(dict.fromkeys(task.dependencies))
            task.acceptance_criteria = list(dict.fromkeys(task.acceptance_criteria))
            if not task.risks:
                task.risks = ["Implementation may introduce regressions and should be validated."]
            task.risks = list(dict.fromkeys(task.risks))

        self._ensure_acyclic(plan)
        plan.tasks.sort(key=lambda task: (len(task.dependencies), task.task_id))
        if not plan.overall_risks:
            plan.overall_risks = [risk for task in plan.tasks for risk in task.risks]
        plan.overall_risks = list(dict.fromkeys(plan.overall_risks))
        return plan

    @staticmethod
    def _ensure_acyclic(plan: PlanResult) -> None:
        """Reject cyclic task dependencies that make execution order impossible."""
        graph = {task.task_id: task.dependencies for task in plan.tasks}
        visiting: set[str] = set()
        visited: set[str] = set()

        def visit(task_id: str) -> None:
            if task_id in visited:
                return
            if task_id in visiting:
                raise ToolExecutionError(f"Plan contains a dependency cycle involving {task_id}.")
            visiting.add(task_id)
            for dependency in graph[task_id]:
                visit(dependency)
            visiting.remove(task_id)
            visited.add(task_id)

        for task_id in graph:
            visit(task_id)
