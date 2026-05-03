# Pawara Branch Agent Evidence
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

## Viva Demonstration Checklist

- Show `context_agent.py` and explain why the agent runs after Intake.
- Show `repo_context_finder.py` and explain attachment-first retrieval.
- Demonstrate the path traversal check using the context evaluation test.
- Explain why bounded snippets help local SLMs stay reliable.
- Show that the Context Agent passes `ContextBundle` forward to Planning.

## Key Defense Point

This contribution proves that the MAS uses a real custom tool to interact with the local repository. The Context Agent does not depend only on LLM memory; it retrieves concrete files and snippets before reasoning.
