# Pawara Branch Agent Evidence

## Assigned Contribution

- Member: Pawara Sasmina
- Branch: `pawara`
- Agent: Context Agent
- Tool: RepoContextFinderTool
- Evaluation: Context retrieval evaluation and attachment handling

## Evidence Files

- `src/flowforge/agents/context_agent.py`
- `src/flowforge/tools/repo_context_finder.py`
- `tests/unit/test_context_agent.py`
- `tests/evals/test_context_eval.py`

## Viva Summary

Pawara can defend the Context Agent as the repository evidence retrieval stage. The agent receives the normalized request from Intake, uses RepoContextFinderTool to retrieve relevant local files, prioritizes user attachments, blocks path traversal attempts, limits snippet size, and passes a structured ContextBundle to the Planning Agent.

## Main Challenge

Keeping repository retrieval useful while avoiding unsafe or excessive file access.

## Resolution

The tool uses attachment-first retrieval, root-bound path checks, large-file skipping, keyword scoring, and bounded snippets.
# Sankalani Branch Agent Evidence

## Assigned Contribution

- Member: Sankalani
- Branch: `sankalani`
- Agent: Planning Agent
- Tool: TaskPlanBuilderTool
- Evaluation: Planning normalization and dependency validation

## Evidence Files

- `src/flowforge/agents/planning_agent.py`
- `src/flowforge/tools/task_plan_builder.py`
- `tests/unit/test_planning_agent.py`
- `tests/evals/test_planning_eval.py`

## Viva Summary

Sankalani can defend the Planning Agent as the stage that converts intake and repository context into an implementation-ready task plan. The agent creates tasks with priorities, dependencies, risks, and acceptance criteria, then TaskPlanBuilderTool validates the generated plan.

## Main Challenge

LLM output can be schema-valid while still containing invalid dependencies or impossible execution order.

## Resolution

The tool rejects self-dependencies, unknown dependencies, and dependency cycles, then normalizes task ordering and de-duplicates risks and acceptance criteria.
