from __future__ import annotations

import re

from flowforge.models.outputs import ContextBundle, IntakeResult, PlanResult


class QaValidatorTool:
    """Apply deterministic QA checks before the final approval call."""

    def run(
        self,
        *,
        intake: IntakeResult,
        context: ContextBundle,
        plan: PlanResult,
        workflow_constraints: list[str] | None = None,
        observability_enabled: bool = False,
    ) -> list[str]:
        """Return rule-based findings for missing or inconsistent details."""
        findings: list[str] = []
        # Core workflow artifacts must be present before deeper quality checks are useful.
        if not intake.goals:
            findings.append("Intake result is missing explicit goals.")
        if not context.selected_snippets:
            findings.append("Context bundle does not contain any selected snippets.")
        if not plan.tasks:
            findings.append("Plan does not contain any tasks.")
        if not plan.overall_risks:
            findings.append("Plan does not contain any overall risks.")
        # Each planned task should carry enough evidence to be testable and risk-aware.
        for task in plan.tasks:
            if not task.acceptance_criteria:
                findings.append(f"Task {task.task_id} is missing acceptance criteria.")
            if not task.risks:
                findings.append(f"Task {task.task_id} is missing risks.")
        # Combine plan and context language so keyword checks see the same evidence reviewers see.
        combined_text = " ".join(
            [
                plan.summary.lower(),
                context.summary.lower(),
                *[constraint.lower() for constraint in context.constraints],
                *[constraint.lower() for constraint in (workflow_constraints or [])],
                *[task.title.lower() for task in plan.tasks],
                *[task.description.lower() for task in plan.tasks],
                *[criterion.lower() for task in plan.tasks for criterion in task.acceptance_criteria],
            ]
        )
        # Tokenization supports exact local-only checks without relying on brittle substring matches.
        combined_tokens = set(re.findall(r"[a-z0-9-]+", combined_text))
        # Local execution is a project requirement, so the final plan must state it clearly.
        if not (
            "offline" in combined_tokens
            or "ollama" in combined_tokens
            or "local-only" in combined_tokens
            or ("local" in combined_tokens and "only" in combined_tokens)
            or "local" in combined_tokens
        ):
            findings.append("Plan should explicitly confirm local-only execution constraints.")
        if not observability_enabled and not {
            "trace",
            "tracing",
            "logging",
            "log",
            "observability",
        }.intersection(combined_tokens):
            findings.append("Plan should provide observability evidence such as tracing or logging coverage.")
        if intake.category == "bug":
            if not any(keyword in combined_text for keyword in ("repro", "root cause", "fix", "regression", "validate")):
                findings.append("Bug plan should cover reproduction, fix validation, or regression protection.")
        elif intake.category == "feature":
            if not any(keyword in combined_text for keyword in ("requirement", "design", "ux", "api", "accessibility", "rollout", "improve")):
                findings.append("Feature plan should cover requirements, design/UX impact, or rollout considerations.")
        return findings
