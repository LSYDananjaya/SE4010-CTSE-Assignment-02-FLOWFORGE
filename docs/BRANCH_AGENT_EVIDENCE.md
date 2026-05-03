# Osanda Branch Agent Evidence

## Assigned Contribution

- Member: Osanda
- Branch: `osanda`
- Agent: Intake Agent
- Tool: IntakeParserTool
- Evaluation: Intake evaluation and malformed input handling

## Evidence Files

- `src/flowforge/agents/intake_agent.py`
- `src/flowforge/tools/intake_parser.py`
- `tests/unit/test_intake_agent.py`
- `tests/evals/test_intake_eval.py`

## Viva Summary

Osanda can defend the Intake Agent as the first stage of the MAS pipeline. The agent normalizes the user request, classifies the work as a bug or feature, estimates severity and scope, extracts goals, and passes a structured IntakeResult to the Context Agent.

## Main Challenge

Preventing noisy or empty user input from reaching the LLM and producing unreliable downstream results.

## Resolution

IntakeParserTool normalizes whitespace, removes blank and duplicate constraints, and rejects requests that are missing meaningful title or description content.
# Yehara Branch Agent Evidence

## Assigned Contribution

- Member: Yehara Dananjaya
- Branch: `yehara`
- Agent: QA Agent
- Tool: QaValidatorTool
- Evaluation: QA validation, tracing, and rubric alignment

## Evidence Files

- `src/flowforge/agents/qa_agent.py`
- `src/flowforge/tools/qa_validator.py`
- `src/flowforge/services/tracing.py`
- `tests/unit/test_qa_agent.py`
- `tests/unit/test_tracing.py`
- `tests/evals/test_qa_eval.py`

## Viva Summary

Yehara can defend the QA Agent as the final quality gate. The agent checks whether the generated plan is complete, local-only, observable, category-aware, and ready for implementation. QaValidatorTool performs deterministic checks so important findings are not lost during LLM review.

## Main Challenge

Making QA approval explainable and aligned with the assignment rubric instead of depending only on model judgment.

## Resolution

The tool checks goals, snippets, tasks, acceptance criteria, risks, local-only evidence, observability coverage, and bug/feature-specific quality signals.
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
