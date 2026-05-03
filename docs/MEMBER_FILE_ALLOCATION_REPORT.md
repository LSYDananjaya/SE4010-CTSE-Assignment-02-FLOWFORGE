# FlowForge Member File Allocation Report

This report assigns each repository file to one team member for contribution evidence and viva clarity.

## Team Members
- Member 1: Pawara Sasmina
- Member 2: Yehara Dananjaya
- Member 3: Sankalani
- Member 4: Osanda

## Allocation Strategy
- Member 1: Intake flow, request handling, launcher input/session controls, intake tests.
- Member 2: Context retrieval, repository/file analysis tools, context tests.
- Member 3: Planning/orchestration core, app entry/config, persistence/reporting, planning tests.
- Member 4: QA/validation, observability, UI rendering, QA/integration/eval ownership.

## Member 1 File Ownership
- `.gitignore`
- `New Text Document.txt`
- `sample_inputs/bug_report_login_timeout.json`
- `sample_inputs/feature_request_export_tasks.json`
- `src/flowforge/__init__.py`
- `src/flowforge/models/requests.py`
- `src/flowforge/agents/intake_agent.py`
- `src/flowforge/tools/intake_parser.py`
- `src/flowforge/launcher/__init__.py`
- `src/flowforge/launcher/models.py`
- `src/flowforge/launcher/input_controller.py`
- `src/flowforge/launcher/request_selector.py`
- `src/flowforge/launcher/project_selector.py`
- `src/flowforge/launcher/prompt_toolkit_io.py`
- `src/flowforge/launcher/state_machine.py`
- `src/flowforge/launcher/app.py`
- `tests/__init__.py`
- `tests/conftest.py`
- `tests/unit/test_intake_agent.py`
- `tests/unit/test_request_selector.py`
- `tests/unit/test_project_selector.py`
- `tests/unit/test_prompt_toolkit_fallback.py`
- `tests/unit/test_launcher_input.py`
- `tests/unit/test_launcher_state_machine.py`
- `tests/unit/test_launcher_renderer.py`
- `tests/evals/test_intake_eval.py`
- `docs/TEAM_CONTRIBUTIONS.md`
- `docs/MEMBER_EVIDENCE_TEMPLATE.md`

## Member 2 File Ownership
- `src/flowforge/agents/context_agent.py`
- `src/flowforge/tools/repo_context_finder.py`
- `src/flowforge/launcher/file_suggester.py`
- `src/flowforge/utils/file_io.py`
- `src/flowforge/models/outputs.py`
- `tests/unit/test_context_agent.py`
- `tests/unit/test_file_suggester.py`
- `tests/evals/test_context_eval.py`
- `tests/fixtures/sample_repo/README.md`
- `tests/fixtures/sample_repo/src/auth_service.py`
- `tests/fixtures/sample_repo/tests/test_auth_service.py`

## Member 3 File Ownership
- `main.py`
- `requirements.txt`
- `README.md`
- `download_qwen35_4b_project.ps1`
- `src/flowforge/config.py`
- `src/flowforge/models/__init__.py`
- `src/flowforge/models/state.py`
- `src/flowforge/agents/planning_agent.py`
- `src/flowforge/tools/task_plan_builder.py`
- `src/flowforge/graph/__init__.py`
- `src/flowforge/graph/router.py`
- `src/flowforge/graph/workflow.py`
- `src/flowforge/services/__init__.py`
- `src/flowforge/services/persistence.py`
- `src/flowforge/services/reporting.py`
- `src/flowforge/llm/__init__.py`
- `src/flowforge/llm/structured_generation.py`
- `src/flowforge/llm/ollama_client.py`
- `src/flowforge/utils/__init__.py`
- `src/flowforge/utils/time.py`
- `src/flowforge/utils/errors.py`
- `tests/unit/test_planning_agent.py`
- `tests/unit/test_workflow.py`
- `tests/unit/test_persistence.py`
- `tests/unit/test_ollama_client.py`
- `tests/evals/test_planning_eval.py`
- `tests/integration/test_main_entrypoint.py`
- `docs/TECHNICAL_REPORT_TEMPLATE.md`

## Member 4 File Ownership
- `src/flowforge/agents/__init__.py`
- `src/flowforge/agents/prompts.py`
- `src/flowforge/agents/qa_agent.py`
- `src/flowforge/tools/__init__.py`
- `src/flowforge/tools/qa_validator.py`
- `src/flowforge/graph/nodes.py`
- `src/flowforge/services/tracing.py`
- `src/flowforge/tui/__init__.py`
- `src/flowforge/tui/app.py`
- `src/flowforge/tui/renderer.py`
- `src/flowforge/tui/theme.py`
- `tests/unit/test_qa_agent.py`
- `tests/unit/test_theme.py`
- `tests/evals/test_qa_eval.py`
- `tests/integration/test_end_to_end_mocked.py`
- `tests/integration/test_end_to_end_live_ollama.py`
- `tests/integration/test_launcher_flow.py`

## Shared Runtime Data (Group-Owned, Generated)
- `data/reports/.gitignore`
- `data/traces/.gitignore`
- `data/traces/.gitkeep`

## Finalization Checklist
- Member names are now filled for repository evidence.
- Ensure each member commits at least once in their owned files.
- Include this file in the report appendix as contribution proof.
