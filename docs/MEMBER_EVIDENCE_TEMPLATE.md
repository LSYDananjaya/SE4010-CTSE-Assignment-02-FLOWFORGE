# FlowForge Member Evidence Pack

This document is ready to be copied into the technical report appendix as individual contribution proof.

## Member: Pawara Sasmina

### Agent Developed

- Agent: `Intake Agent`
- Files: `src/flowforge/agents/intake_agent.py`, `src/flowforge/agents/prompts.py`
- Prompt/constraint highlights:
  - Forces grounded classification from only the raw request, with no repository hallucination.
  - Extracts explicit goals and missing information so later agents do not invent requirements.

### Tool Implemented

- Tool: `IntakeParserTool`
- File: `src/flowforge/tools/intake_parser.py`
- Type-hint and docstring evidence:
  - `run(self, request: UserRequest) -> ParsedRequest`
  - `ParsedRequest` is a typed `BaseModel` used as a schema boundary before prompting.
- Error-handling evidence:
  - Rejects requests that become empty after whitespace normalization.
  - Removes duplicate or blank constraints before they reach the model.

### Testing/Evaluation Contribution

- Evaluation files: `tests/evals/test_intake_eval.py`
- Unit files: `tests/unit/test_intake_agent.py`
- Assertions added:
  - Validates required intake fields for a correctly structured request.
  - Rejects whitespace-only descriptions to prevent malformed requests from silently reaching the LLM.

### Challenges Faced

- Challenge: raw user requests can pass schema validation while still being semantically empty after normalization.
- Resolution: added post-normalization validation inside the tool instead of relying only on the input schema.
- Verification: `tests/unit/test_intake_agent.py` and `tests/evals/test_intake_eval.py` both cover the malformed-input path.

## Member: Yehara Dananjaya

### Agent Developed

- Agent: `Context Agent`
- Files: `src/flowforge/agents/context_agent.py`, `src/flowforge/agents/prompts.py`
- Prompt/constraint highlights:
  - Requires the agent to use only retrieved local candidates and to respect explicitly attached files first.
  - Encourages concise, evidence-based context summaries instead of broad repository narration.

### Tool Implemented

- Tool: `RepoContextFinderTool`
- File: `src/flowforge/tools/repo_context_finder.py`
- Type-hint and docstring evidence:
  - Uses typed models `RetrievalResult` and `RetrievalCandidate`.
  - Public interface declares `repo_path`, `query`, `constraints`, and `attachments`.
- Error-handling evidence:
  - Blocks attachment path traversal outside the repository root.
  - Skips oversized or unreadable files and reports missing attachments safely.

### Testing/Evaluation Contribution

- Evaluation files: `tests/evals/test_context_eval.py`
- Unit files: `tests/unit/test_context_agent.py`
- Assertions added:
  - Ensures snippet output stays within the configured content bound.
  - Rejects path-escape attempts such as `../../outside.txt`.

### Challenges Faced

- Challenge: retrieving enough context for planning without overloading a small model with irrelevant repository files.
- Resolution: used attachment-first prioritization, file-type filtering, bounded snippet sizes, and keyword scoring.
- Verification: context unit tests cover attached files, empty-context fallback, missing attachments, and deterministic fallback when structured generation fails.

## Member: Sankalani

### Agent Developed

- Agent: `Planning Agent`
- Files: `src/flowforge/agents/planning_agent.py`, `src/flowforge/agents/prompts.py`
- Prompt/constraint highlights:
  - Separates bug-plan behavior from feature-plan behavior.
  - Forces task dependencies, acceptance criteria, risks, and local-only constraints into the prompt context.

### Tool Implemented

- Tool: `TaskPlanBuilderTool`
- File: `src/flowforge/tools/task_plan_builder.py`
- Type-hint and docstring evidence:
  - Typed interface `run(self, plan: PlanResult) -> PlanResult`.
  - Operates on structured `PlanResult` and `PlannedTask` models instead of raw dictionaries.
- Error-handling evidence:
  - Rejects self-dependencies, unknown dependencies, and dependency cycles.
  - Deduplicates acceptance criteria and risks to stabilize plan output.

### Testing/Evaluation Contribution

- Evaluation files: `tests/evals/test_planning_eval.py`
- Unit files: `tests/unit/test_planning_agent.py`
- Assertions added:
  - Confirms dependency references only point to valid task IDs.
  - Rejects cyclic plans that would make execution order impossible.

### Challenges Faced

- Challenge: structured plan output can still be internally inconsistent even when it validates against the schema.
- Resolution: added deterministic graph validation after LLM generation rather than trusting model output as-is.
- Verification: planning tests now cover both valid dependency ordering and explicit cycle rejection.

## Member: Osanda

### Agent Developed

- Agent: `QA Agent`
- Files: `src/flowforge/agents/qa_agent.py`, `src/flowforge/agents/prompts.py`
- Prompt/constraint highlights:
  - Explicitly combines deterministic QA findings with structured LLM review.
  - Uses category-aware validation criteria for bug fixes versus features and checks local-only plus observability expectations.

### Tool Implemented

- Tool: `QaValidatorTool`
- Files: `src/flowforge/tools/qa_validator.py`, `src/flowforge/services/tracing.py`
- Type-hint and docstring evidence:
  - Deterministic QA interface accepts typed `IntakeResult`, `ContextBundle`, `PlanResult`, and execution context.
  - Trace writer stores structured per-event metadata instead of plain strings only.
- Error-handling evidence:
  - Flags missing acceptance criteria, missing risks, absent local-only language, and absent observability evidence.
  - Captures failure causes inside trace payloads for debugging and demo visibility.

### Testing/Evaluation Contribution

- Evaluation files: `tests/evals/test_qa_eval.py`
- Unit files: `tests/unit/test_qa_agent.py`, `tests/unit/test_tracing.py`
- Assertions added:
  - Detects missing local-only and observability evidence in weak plans.
  - Confirms trace files persist agent input summaries, tool summaries, fallback flags, and failure fields.

### Challenges Faced

- Challenge: a basic pass/fail QA stage is not enough for the assignment rubric because it hides why a run was approved or rejected.
- Resolution: extended the deterministic validator and the trace writer so the system exposes inputs, tool usage, LLM outputs, and failure causes.
- Verification: `tests/unit/test_tracing.py` and `tests/evals/test_qa_eval.py` confirm the richer observability path.
