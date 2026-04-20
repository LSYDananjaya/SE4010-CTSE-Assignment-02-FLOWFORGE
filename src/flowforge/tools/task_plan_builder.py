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
            task.risks = list(dict.fromkeys(task.risks))

        plan.tasks.sort(key=lambda task: (len(task.dependencies), task.task_id))
        plan.overall_risks = list(dict.fromkeys(plan.overall_risks))
        return plan
