from __future__ import annotations


INTAKE_PROMPT = """
Classify and normalize the software engineering request.
Keep the summary short and extract explicit goals plus missing information.
"""

CONTEXT_PROMPT = """
Select the most relevant repository snippets for the request.
Prefer files that directly inform implementation and constraints.
Respect explicitly attached files first when they exist.
"""

PLANNING_PROMPT = """
Produce an implementation-ready engineering plan with dependencies, priorities, acceptance criteria, and risks.
Keep the task list concise and deterministic.
Differentiate bug-fix plans from feature/improvement plans.
"""

QA_PROMPT = """
Validate the plan for completeness, consistency, local-only compliance, observability coverage, and test readiness.
Return approval only if the plan is ready for implementation.
Use the request category to apply an appropriate rubric for bug fixes versus features.
"""
