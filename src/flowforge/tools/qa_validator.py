from __future__ import annotations

from flowforge.models.outputs import ContextBundle, IntakeResult, PlanResult


class QaValidatorTool:
    """Apply deterministic QA checks before the final approval call."""

    def run(self, *, intake: IntakeResult, context: ContextBundle, plan: PlanResult) -> list[str]:
        """Return rule-based findings for missing or inconsistent details."""
        findings: list[str] = []
        if not intake.goals:
            findings.append("Intake result is missing explicit goals.")
        if not context.selected_snippets:
            findings.append("Context bundle does not contain any selected snippets.")
        if not plan.tasks:
            findings.append("Plan does not contain any tasks.")
        if not plan.overall_risks:
            findings.append("Plan does not contain any overall risks.")
        for task in plan.tasks:
            if not task.acceptance_criteria:
                findings.append(f"Task {task.task_id} is missing acceptance criteria.")
            if not task.risks:
                findings.append(f"Task {task.task_id} is missing risks.")
        combined_text = " ".join(
            [
                plan.summary.lower(),
                *[task.title.lower() for task in plan.tasks],
                *[task.description.lower() for task in plan.tasks],
                *[criterion.lower() for task in plan.tasks for criterion in task.acceptance_criteria],
            ]
        )
        if intake.category == "bug":
            if not any(keyword in combined_text for keyword in ("repro", "root cause", "fix", "regression", "validate")):
                findings.append("Bug plan should cover reproduction, fix validation, or regression protection.")
        elif intake.category == "feature":
            if not any(keyword in combined_text for keyword in ("requirement", "design", "ux", "api", "accessibility", "rollout", "improve")):
                findings.append("Feature plan should cover requirements, design/UX impact, or rollout considerations.")
        return findings
