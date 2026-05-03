# Planning Agent Notes

This note summarizes the Planning Agent contribution area for project evidence
and future maintenance.

## Responsibility

The Planning Agent converts intake output and repository context into an
implementation-ready task plan. It prepares the LLM prompt, sends the request
for structured planning output, and passes the result through the
TaskPlanBuilderTool for deterministic cleanup.

## Current Flow

1. Validate that intake and context outputs are available.
2. Build a compact prompt with the request category, goals, constraints, and
   selected code snippets.
3. Request a structured PlanResult from the LLM client.
4. Normalize tasks, dependencies, acceptance criteria, and risks through the
   planning tool.
5. Record trace summaries for reporting and debugging.

## Fallback Behavior

If structured generation fails because the local Ollama response cannot be
parsed, the agent builds a deterministic fallback plan. Bug requests focus on
reproduction, implementation, and regression validation. Feature requests focus
on scope confirmation, implementation, and edge-case validation.

## Testing Focus

Planning tests should confirm prompt context, dependency validation, fallback
planning, and trace metadata. This keeps the agent behavior clear without
depending on a live LLM during unit tests.
