# Team Contribution Split (4 Members)

This project is implemented by one codebase, but for assignment compliance each member is assigned ownership of one agent, one tool, and dedicated evaluation coverage.

## Member Allocation

| Member | Agent Ownership | Tool Ownership | Evaluation Ownership | Primary Files |
|---|---|---|---|---|
| Member 1 (Name/ID) | Intake Agent | Intake Parser Tool | Intake evaluation tests | `src/flowforge/agents/intake_agent.py`, `src/flowforge/tools/intake_parser.py`, `tests/evals/test_intake_eval.py`, `tests/unit/test_intake_agent.py` |
| Member 2 (Name/ID) | Context Agent | Repo Context Finder Tool | Context evaluation tests | `src/flowforge/agents/context_agent.py`, `src/flowforge/tools/repo_context_finder.py`, `tests/evals/test_context_eval.py`, `tests/unit/test_context_agent.py` |
| Member 3 (Name/ID) | Planning Agent | Task Plan Builder Tool | Planning evaluation tests | `src/flowforge/agents/planning_agent.py`, `src/flowforge/tools/task_plan_builder.py`, `tests/evals/test_planning_eval.py`, `tests/unit/test_planning_agent.py` |
| Member 4 (Name/ID) | QA Agent | QA Validator Tool | QA evaluation tests | `src/flowforge/agents/qa_agent.py`, `src/flowforge/tools/qa_validator.py`, `tests/evals/test_qa_eval.py`, `tests/unit/test_qa_agent.py` |

## Unified Group Components

- Shared orchestration graph: `src/flowforge/graph/workflow.py`
- Shared state model: `src/flowforge/models/state.py`
- Shared tracing/observability: `src/flowforge/services/tracing.py`
- Shared reporting/persistence: `src/flowforge/services/reporting.py`, `src/flowforge/services/persistence.py`
- Integration testing harness: `tests/integration/`

## Evidence Checklist Per Member

Each member should provide proof for:

1. Agent built
- Agent prompt strategy and constraints used.
- Why this agent design fits local SLM behavior.

2. Tool built
- Type hints and docstrings present.
- Error handling decisions.

3. Testing/evaluation contributed
- At least one evaluation test for correctness.
- At least one security/robustness-oriented assertion.

4. Challenges faced
- Short note: issue, root cause, fix.

## Submission Notes

- Fill actual student names and IDs in the table above.
- Keep commit evidence by making at least one commit per member touching their owned files.
- In the report, include this table and short per-member contribution paragraphs.
