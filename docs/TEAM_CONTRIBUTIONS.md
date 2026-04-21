# FlowForge Team Contribution Split

FlowForge is a single local-first codebase, but the assignment requires each student to demonstrate ownership of one agent, one custom tool, and one evaluation stream. The project is organized so that each member can defend a distinct technical slice while still contributing to one integrated LangGraph workflow.

## Repository

- GitHub: https://github.com/LSYDananjaya/SE4010-CTSE-Assignment-02-FLOWFORGE

## Team Allocation

| Member | Agent Ownership | Tool Ownership | Evaluation Ownership | Core Evidence Files |
|---|---|---|---|---|
| Pawara Sasmina | Intake Agent | IntakeParserTool | Intake evaluation and launcher validation | `src/flowforge/agents/intake_agent.py`, `src/flowforge/tools/intake_parser.py`, `tests/unit/test_intake_agent.py`, `tests/evals/test_intake_eval.py` |
| Yehara Dananjaya | Context Agent | RepoContextFinderTool | Context retrieval evaluation and attachment handling | `src/flowforge/agents/context_agent.py`, `src/flowforge/tools/repo_context_finder.py`, `tests/unit/test_context_agent.py`, `tests/evals/test_context_eval.py` |
| Sankalani | Planning Agent | TaskPlanBuilderTool | Planning normalization and dependency validation | `src/flowforge/agents/planning_agent.py`, `src/flowforge/tools/task_plan_builder.py`, `tests/unit/test_planning_agent.py`, `tests/evals/test_planning_eval.py` |
| Osanda | QA Agent | QaValidatorTool | QA validation, tracing, and end-to-end rubric checks | `src/flowforge/agents/qa_agent.py`, `src/flowforge/tools/qa_validator.py`, `src/flowforge/services/tracing.py`, `tests/unit/test_qa_agent.py`, `tests/unit/test_tracing.py`, `tests/evals/test_qa_eval.py` |

## Shared Group Components

- Workflow orchestration: `src/flowforge/graph/workflow.py`, `src/flowforge/graph/nodes.py`, `src/flowforge/graph/router.py`
- Shared state and schema contracts: `src/flowforge/models/state.py`, `src/flowforge/models/outputs.py`, `src/flowforge/models/requests.py`
- Persistence and reporting: `src/flowforge/services/persistence.py`, `src/flowforge/services/reporting.py`
- Launcher and TUI: `src/flowforge/launcher/`, `src/flowforge/tui/`
- Integration harness: `tests/integration/`

## Per-Member Evidence Summary

### Pawara Sasmina

- Designed the Intake Agent prompt to force conservative classification, explicit goals, and missing-information extraction for small local models.
- Implemented `IntakeParserTool` with strict normalization, duplicate constraint removal, and rejection of whitespace-only requests after sanitization.
- Added evaluation coverage for blank/noisy requests and launcher-facing intake behavior.
- Main challenge: preventing malformed user input from reaching the LLM layer and causing low-signal outputs.

### Yehara Dananjaya

- Designed the Context Agent to prioritize attached files and limit context to high-signal snippets.
- Implemented `RepoContextFinderTool` with attachment-first retrieval, path-traversal blocking, large-file skipping, and improved keyword scoring.
- Added evaluation coverage for snippet bounds and malicious attachment escape attempts.
- Main challenge: keeping retrieval useful without reading too much of the repository or trusting unsafe paths.

### Sankalani

- Designed the Planning Agent prompt to separate bug-fix planning from feature-planning logic.
- Implemented `TaskPlanBuilderTool` to validate dependency references, remove duplicates, and reject dependency cycles.
- Added evaluation coverage for invalid dependency graphs and cycle detection.
- Main challenge: converting free-form structured LLM output into a stable execution plan that remains implementable and deterministic.

### Osanda

- Designed the QA Agent prompt and deterministic validation strategy for rubric alignment.
- Implemented `QaValidatorTool` checks for acceptance criteria, risks, local-only compliance, category-specific quality, and observability expectations.
- Upgraded `JsonTraceWriter` tracing so runs now capture agent input summaries, tool input/output summaries, fallback usage, LLM output summaries, and failure causes.
- Added evaluation coverage for missing observability evidence and richer trace payloads.

## Submission Notes

- Each member can demonstrate one owned agent, one owned tool, and one owned evaluation file during the viva.
- The report should include this table plus the expanded evidence in `docs/MEMBER_EVIDENCE_TEMPLATE.md`.
- The demo should explicitly show the trace file and explain which agent/tool pair belongs to which team member.
