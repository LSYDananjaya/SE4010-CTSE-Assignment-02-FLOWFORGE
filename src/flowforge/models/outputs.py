from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


Priority = Literal["low", "medium", "high"]
Severity = Literal["low", "medium", "high"]
Scope = Literal["backend", "frontend", "fullstack", "unknown"]


class IntakeResult(BaseModel):
    """Normalized request produced by the Intake Agent."""

    category: Literal["bug", "feature"]
    severity: Severity
    scope: Scope
    goals: list[str] = Field(default_factory=list)
    missing_information: list[str] = Field(default_factory=list)
    summary: str


class FileSnippet(BaseModel):
    """Snippet of local repository context."""

    path: str
    language: str
    reason: str
    content: str


class RetrievalCandidate(BaseModel):
    """Raw retrieval candidate returned by the deterministic context tool."""

    path: str
    score: int
    language: str
    content: str


class ContextBundle(BaseModel):
    """Validated repository context for planning."""

    files_considered: int
    selected_snippets: list[FileSnippet] = Field(default_factory=list)
    constraints: list[str] = Field(default_factory=list)
    summary: str


class PlannedTask(BaseModel):
    """Implementation-ready unit of work."""

    task_id: str
    title: str
    description: str
    priority: Priority
    dependencies: list[str] = Field(default_factory=list)
    acceptance_criteria: list[str] = Field(default_factory=list)
    risks: list[str] = Field(default_factory=list)
    owner: str


class PlanResult(BaseModel):
    """Structured engineering plan returned by the Planning Agent."""

    summary: str
    tasks: list[PlannedTask] = Field(default_factory=list)
    overall_risks: list[str] = Field(default_factory=list)


class QaResult(BaseModel):
    """Validation result returned by the QA Agent."""

    approved: bool
    findings: list[str] = Field(default_factory=list)
    rubric_checks: dict[str, bool] = Field(default_factory=dict)
    summary: str


class ArtifactPaths(BaseModel):
    """File locations for generated reports and traces."""

    markdown_report: str
    json_report: str
    trace_file: str
