# FlowForge Demo Video Script

Target length: `4:00` to `4:45`

## 0:00 - 0:30 Intro

- Open with the project title: `FlowForge`.
- State the problem in one sentence:
  - "FlowForge is a local multi-agent system that turns raw software requests into repository-aware implementation plans."
- Mention the local-only stack:
  - Ollama
  - LangGraph
  - Python
  - SQLite
  - JSONL tracing

## 0:30 - 1:00 Show Local Setup

- Run `ollama list`.
- Briefly show that the model is available locally.
- Open the repository and point out:
  - `src/flowforge/agents/`
  - `src/flowforge/tools/`
  - `tests/evals/`

## 1:00 - 2:00 Run the Workflow

- Run:

```powershell
python main.py `
  --repo-path "." `
  --input-file "sample_inputs\bug_report_login_timeout.json" `
  --live-ollama
```

- While it runs, explain the 4-agent sequence:
  - Intake Agent
  - Context Agent
  - Planning Agent
  - QA Agent

## 2:00 - 2:45 Show Output Artifacts

- Open the generated Markdown report in `data/reports/`.
- Open the generated JSON report.
- Open `data/app.db` or explain that it stores run history and recent project tracking.

## 2:45 - 3:35 Show Observability

- Open the latest file in `data/traces/`.
- Explain the important trace fields:
  - `agent_input_summary`
  - `tool_name`
  - `tool_input_summary`
  - `tool_output_summary`
  - `fallback_used`
  - `llm_output_summary`
  - `failure_cause`

- State clearly that this is the system’s AgentOps evidence.

## 3:35 - 4:15 Show Testing

- Run:

```powershell
python -m pytest -q
```

- Explain that the project includes:
  - unit tests
  - integration tests
  - per-agent evaluation tests

## 4:15 - 4:45 Member Contributions

- Close with one sentence per member:
  - Pawara Sasmina: Intake Agent and IntakeParserTool
  - Yehara Dananjaya: Context Agent and RepoContextFinderTool
  - Sankalani: Planning Agent and TaskPlanBuilderTool
  - Osanda: QA Agent, QaValidatorTool, and tracing/observability

- Final line:
  - "FlowForge satisfies the assignment with a fully local, tool-using, observable multi-agent workflow."
