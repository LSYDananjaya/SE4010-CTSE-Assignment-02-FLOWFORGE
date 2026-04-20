# FlowForge

FlowForge is a local multi-agent workflow assistant for software engineering requests. It accepts a bug report or feature request, analyzes a local repository, produces an implementation-ready plan, validates the result, and stores reports plus execution traces on the local machine.

## Core Workflow

FlowForge runs four sequential agents through a LangGraph workflow:

1. `Intake Agent` converts a raw request into structured input.
2. `Context Agent` retrieves relevant code and repository context.
3. `Planning Agent` builds an implementation-oriented task plan.
4. `QA Agent` validates completeness, consistency, and rubric alignment.

The workflow uses typed Pydantic models for shared state, writes run metadata to SQLite, stores reports in Markdown and JSON, and records execution traces as JSONL.

## Tech Stack

- Python 3.11+
- LangGraph
- Pydantic v2
- Requests
- Rich
- prompt_toolkit
- Pytest
- Ollama for local structured generation

## Project Structure

```text
main.py                             CLI entry point
requirements.txt                    Python dependencies
sample_inputs/                      Example bug reports and feature requests
src/flowforge/
  agents/                           Agent implementations and prompts
  graph/                            LangGraph node wiring and workflow assembly
  launcher/                         Interactive request selection flow
  llm/                              Ollama client and structured generation logic
  models/                           Request, output, and workflow state models
  services/                         Persistence, reporting, and tracing helpers
  tools/                            Deterministic tools used by agents
  tui/                              Rich-based terminal rendering
  utils/                            Shared support utilities
tests/
  unit/                             Unit tests
  integration/                      End-to-end and launcher flow tests
  evals/                            Agent evaluation tests
  fixtures/                         Test repositories and sample fixtures
data/
  reports/                          Generated Markdown and JSON reports
  traces/                           Generated JSONL traces
  app.db                            Run metadata database
logs/                               Local execution logs
ollama_models/                      Optional local model artifacts
```

## Setup

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
ollama pull qwen2.5:3b
```

If your PowerShell execution policy blocks activation, open PowerShell with the appropriate local policy or activate the environment using another supported shell.

## Running FlowForge

### Direct CLI Mode

Use direct mode when you already know the repository and request file to analyze:

```powershell
python main.py `
  --repo-path "C:\path\to\local\repo" `
  --input-file "sample_inputs\bug_report_login_timeout.json" `
  --live-ollama
```

Optional Rich terminal rendering:

```powershell
python main.py `
  --repo-path "C:\path\to\local\repo" `
  --input-file "sample_inputs\feature_request_export_tasks.json" `
  --live-ollama `
  --tui
```

### Interactive Launcher Mode

Run without `--repo-path` and `--input-file` to open the interactive launcher:

```powershell
python main.py --live-ollama
```

`prompt_toolkit` is required for this mode. It is already included in `requirements.txt`.

## Output Files

Each run writes artifacts under `data/`:

- `data/reports/*.md` for the human-readable report
- `data/reports/*.json` for the structured report
- `data/traces/*.jsonl` for workflow traces
- `data/app.db` for persistent run history and recent project tracking

These generated artifacts are ignored by Git through the repository `.gitignore` files so the folder structure can remain in version control without committing local runtime output.

## Testing

Run the default automated test suite:

```powershell
python -m pytest -q
```

Live Ollama integration test:

```powershell
$env:FLOWFORGE_LIVE_OLLAMA = "1"
python -m pytest tests\integration\test_end_to_end_live_ollama.py -q
```

## Notes

- FlowForge expects a local Ollama server when running with `--live-ollama`.
- The current application raises an error if `--live-ollama` is omitted outside tests.
- Reports, traces, logs, the local SQLite database, virtual environments, and local Ollama assets are intentionally excluded from Git tracking.
