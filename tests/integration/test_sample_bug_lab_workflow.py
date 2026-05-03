from __future__ import annotations

from pathlib import Path

from flowforge.agents.intake_agent import IntakeAgent
from flowforge.graph.workflow import FlowForgeWorkflow
from flowforge.models.requests import UserRequest
from flowforge.models.state import WorkflowState
from flowforge.tools.intake_parser import IntakeParserTool


PROJECT_ROOT = Path(__file__).resolve().parents[2]
BUG_LAB_ROOT = PROJECT_ROOT / "examples" / "sample_bug_lab"


def test_sample_bug_lab_end_to_end_mocked_run_uses_attached_backend_file() -> None:
    responses = [
        {
            "category": "bug",
            "severity": "high",
            "scope": "backend",
            "goals": ["Patch auth protection and input handling"],
            "missing_information": [],
            "summary": "Fix backend auth and payload handling bugs.",
        },
        {
            "files_considered": 2,
            "selected_snippets": [
                {
                    "path": "server/src/routes/auth.ts",
                    "language": "ts",
                    "reason": "Contains the auth bypass logic",
                    "content": "router.get('/session', (_req, res) => res.json({ authenticated: true }));",
                }
            ],
            "constraints": ["Keep changes local"],
            "summary": "Relevant backend auth file found.",
        },
        {
            "summary": "Plan auth hardening and null safety fixes.",
            "tasks": [
                {
                    "task_id": "T1",
                    "title": "Harden session route",
                    "description": "Require session validation before returning authenticated state.",
                    "priority": "high",
                    "dependencies": [],
                    "acceptance_criteria": ["Unauthorized users cannot access protected task routes"],
                    "risks": ["Regression in local auth flow"],
                    "owner": "Student 3",
                }
            ],
            "overall_risks": ["Regression in local auth flow"],
        },
        {
            "approved": True,
            "findings": [],
            "rubric_checks": {
                "security_scope": True,
                "backend_context": True,
                "observability": True,
                "tests_present": True,
            },
            "summary": "Auth hardening plan approved.",
        },
    ]
    llm = __import__("tests.conftest", fromlist=["StubLLM"]).StubLLM(responses)
    workflow = FlowForgeWorkflow.from_stub_llm(llm)

    result = workflow.run(
        UserRequest(
            title="admin route auth bug",
            description="Users can access protected task endpoints without a valid session in @server/src/routes/auth.ts",
            request_type="bug",
            constraints=["Keep changes local"],
            reporter="security-qa",
            repo_path=str(BUG_LAB_ROOT),
            attachments=["server/src/routes/auth.ts"],
        )
    )

    assert result.workflow_status == "completed"
    assert result.context_bundle is not None
    assert result.context_bundle.selected_snippets[0].path == "server/src/routes/auth.ts"
    assert result.plan_result is not None
    assert "auth" in result.plan_result.summary.lower()


def test_sample_bug_lab_intake_fallback_classifies_varied_bug_prompts() -> None:
    requests = [
        UserRequest(
            title="critical broken auth bypass bug",
            description="Server auth route fails safely and lets any user access admin data in @server/src/routes/auth.ts",
            request_type="bug",
            constraints=[],
            reporter="qa",
            repo_path=str(BUG_LAB_ROOT),
            attachments=["server/src/routes/auth.ts"],
        ),
        UserRequest(
            title="improve task modal validation",
            description="Review UI issues in @client/src/components/EditTaskModal.tsx",
            request_type="feature",
            constraints=[],
            reporter="pm",
            repo_path=str(BUG_LAB_ROOT),
            attachments=["client/src/components/EditTaskModal.tsx"],
        ),
        UserRequest(
            title="fullstack status mismatch bug",
            description=(
                "Fix the fullstack status mismatch between @client/src/api/tasks.ts and @shared/types.ts"
            ),
            request_type="bug",
            constraints=[],
            reporter="qa",
            repo_path=str(BUG_LAB_ROOT),
            attachments=["client/src/api/tasks.ts", "shared/types.ts"],
        ),
    ]

    class InvalidStructuredLlm:
        def generate_structured(self, **kwargs):  # type: ignore[no-untyped-def]
            raise ValueError("structured validation failed for test")

    agent = IntakeAgent(llm_client=InvalidStructuredLlm(), tool=IntakeParserTool())
    results = [agent.run(WorkflowState.initial(request=request)).intake_result for request in requests]

    assert results[0] is not None and results[0].severity == "high" and results[0].scope == "backend"
    assert results[1] is not None and results[1].severity == "medium" and results[1].scope == "frontend"
    assert results[2] is not None and results[2].scope == "backend"
