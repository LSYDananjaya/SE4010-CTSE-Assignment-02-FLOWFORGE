from __future__ import annotations

from pathlib import Path

from flowforge.graph.workflow import FlowForgeWorkflow
from flowforge.models.requests import UserRequest
from flowforge.services.persistence import PersistenceService
from flowforge.services.reporting import ReportingService
from flowforge.services.tracing import JsonTraceWriter


def test_end_to_end_mocked_generates_report_and_trace(sample_repo, tmp_path: Path) -> None:
    responses = [
        {
            "category": "bug",
            "severity": "high",
            "scope": "backend",
            "goals": ["Fix timeout"],
            "missing_information": [],
            "summary": "Fix timeout.",
        },
        {
            "files_considered": 2,
            "selected_snippets": [
                {
                    "path": "src/auth_service.py",
                    "language": "python",
                    "reason": "Relevant auth logic",
                    "content": "def login(username: str, password: str) -> bool:\n    return bool(username and password)",
                }
            ],
            "constraints": [],
            "summary": "Auth file found.",
        },
        {
            "summary": "Plan fix.",
            "tasks": [
                {
                    "task_id": "T1",
                    "title": "Patch timeout",
                    "description": "Update timeout handling.",
                    "priority": "high",
                    "dependencies": [],
                    "acceptance_criteria": ["Timeout bug fixed"],
                    "risks": ["Regression"],
                    "owner": "Student 3",
                }
            ],
            "overall_risks": ["Regression"],
        },
        {
            "approved": True,
            "findings": [],
            "rubric_checks": {
                "four_agents": True,
                "local_only": True,
                "observability": True,
                "tests_present": True,
            },
            "summary": "Looks good.",
        },
    ]
    llm = __import__("tests.conftest", fromlist=["StubLLM"]).StubLLM(responses)
    trace_writer = JsonTraceWriter(base_dir=tmp_path / "data")
    workflow = FlowForgeWorkflow.from_stub_llm(llm, trace_writer=trace_writer)
    persistence = PersistenceService(base_dir=tmp_path / "data")
    reporting = ReportingService(base_dir=tmp_path / "data")

    result = workflow.run(
        UserRequest(
            title="Login timeout bug",
            description="Fix login timeout.",
            request_type="bug",
            constraints=["Local only"],
            reporter="qa",
            repo_path=str(sample_repo),
        )
    )
    artifacts = reporting.write_reports(result)
    persistence.record_run(
        run_id=result.run_id,
        request_title=result.request.title,
        workflow_status=result.workflow_status,
        qa_approved=bool(result.qa_result and result.qa_result.approved),
        artifacts=artifacts,
    )

    assert Path(artifacts.markdown_report).exists()
    assert Path(artifacts.json_report).exists()
    assert Path(result.trace_file).exists()
    assert persistence.fetch_runs()


def test_end_to_end_mocked_external_repo_feature_request_uses_attached_component(tmp_path: Path) -> None:
    external_repo = tmp_path / "repos" / "findassure"
    component_dir = external_repo / "src" / "components"
    component_dir.mkdir(parents=True)
    (component_dir / "CategoryPicker.tsx").write_text(
        "export const ITEM_CATEGORIES = ['Books', 'Electronics'];\n"
        "export function CategoryPicker() { return null; }\n",
        encoding="utf-8",
    )
    responses = [
        {
            "category": "feature",
            "severity": "medium",
            "scope": "frontend",
            "goals": ["Improve CategoryPicker"],
            "missing_information": [],
            "summary": "Review CategoryPicker improvements.",
        },
        {
            "files_considered": 1,
            "selected_snippets": [
                {
                    "path": "src/components/CategoryPicker.tsx",
                    "language": "tsx",
                    "reason": "Explicitly attached by the user",
                    "content": "export function CategoryPicker() { return null; }",
                }
            ],
            "constraints": [],
            "summary": "Attached component found.",
        },
        {
            "summary": "Plan UI and accessibility improvements.",
            "tasks": [
                {
                    "task_id": "T1",
                    "title": "Improve CategoryPicker accessibility",
                    "description": "Add accessibility metadata and responsive sizing.",
                    "priority": "medium",
                    "dependencies": [],
                    "acceptance_criteria": ["Accessibility improvements are identified"],
                    "risks": ["UI behavior changes"],
                    "owner": "Student 3",
                }
            ],
            "overall_risks": ["UI behavior changes"],
        },
        {
            "approved": True,
            "findings": [],
            "rubric_checks": {
                "feature_scope": True,
                "ux_impact": True,
                "observability": True,
                "tests_present": True,
            },
            "summary": "Feature plan approved.",
        },
    ]
    llm = __import__("tests.conftest", fromlist=["StubLLM"]).StubLLM(responses)
    workflow = FlowForgeWorkflow.from_stub_llm(llm)

    result = workflow.run(
        UserRequest(
            title="what are the improvements i can do on",
            description="what are the improvements i can do on @src/components/CategoryPicker.tsx",
            request_type="feature",
            constraints=[],
            reporter="qa",
            repo_path=str(external_repo),
            attachments=["src/components/CategoryPicker.tsx"],
        )
    )

    assert result.workflow_status == "completed"
    assert result.context_bundle is not None
    assert result.context_bundle.selected_snippets[0].path == "src/components/CategoryPicker.tsx"
    assert result.request.repo_path == str(external_repo)
    assert result.plan_result is not None
    assert "accessibility" in result.plan_result.summary.lower() or "ui" in result.plan_result.summary.lower()


def test_end_to_end_mocked_recovers_from_invalid_intake_enum(sample_repo) -> None:
    target = sample_repo / "src" / "components"
    target.mkdir(parents=True)
    (target / "FeatureCard.tsx").write_text(
        "export function FeatureCard() { return null; }\n",
        encoding="utf-8",
    )
    responses = [
        {
            "category": "feature",
            "severity": "unknown",
            "scope": "fullstack",
            "goals": ["Review FeatureCard improvements"],
            "missing_information": [],
            "summary": "Review FeatureCard improvements.",
        },
        {
            "files_considered": 1,
            "selected_snippets": [
                {
                    "path": "src/auth_service.py",
                    "language": "python",
                    "reason": "Fallback fixture file",
                    "content": "def login(username: str, password: str) -> bool:\n    return bool(username and password)",
                }
            ],
            "constraints": [],
            "summary": "Context found.",
        },
        {
            "summary": "Plan improvements.",
            "tasks": [
                {
                    "task_id": "T1",
                    "title": "Review target component",
                    "description": "Review the attached target and identify improvements.",
                    "priority": "medium",
                    "dependencies": [],
                    "acceptance_criteria": ["Improvements are clearly identified"],
                    "risks": [],
                    "owner": "Student 3",
                }
            ],
            "overall_risks": [],
        },
        {
            "approved": True,
            "findings": [],
            "rubric_checks": {"feature_quality": True, "observability": True},
            "summary": "Approved.",
        },
    ]
    llm = __import__("tests.conftest", fromlist=["StubLLM"]).StubLLM(responses)
    workflow = FlowForgeWorkflow.from_stub_llm(llm)

    result = workflow.run(
        UserRequest(
            title="what are the improvements can be done on",
            description="what are the improvements can be done on @src/components/FeatureCard.tsx",
            request_type="feature",
            constraints=[],
                reporter="qa",
                repo_path=str(sample_repo),
                attachments=["src/components/FeatureCard.tsx"],
            )
        )

    assert result.workflow_status == "completed"
    assert result.intake_result is not None
    assert result.intake_result.severity == "medium"
    assert result.trace_context["intake"]["fallback_used"] is True
