from __future__ import annotations

from pydantic import BaseModel

from flowforge.models.requests import UserRequest
from flowforge.utils.errors import ToolExecutionError


class ParsedRequest(BaseModel):
    """Sanitized request used by the Intake Agent prompt."""

    title: str
    description: str
    request_type: str
    constraints: list[str]


class IntakeParserTool:
    """Sanitize and normalize raw request fields."""

    def run(self, request: UserRequest) -> ParsedRequest:
        """Return a sanitized view of the request for prompting."""
        try:
            title = " ".join(request.title.split())
            description = " ".join(request.description.split())
            if not title or not description:
                raise ToolExecutionError("Request is missing meaningful title or description after normalization.")
            constraints = list(dict.fromkeys(constraint.strip() for constraint in request.constraints if constraint.strip()))
            return ParsedRequest(
                title=title,
                description=description,
                request_type=request.request_type.lower(),
                constraints=constraints,
            )
        except Exception as exc:  # noqa: BLE001
            if isinstance(exc, ToolExecutionError):
                raise
            raise ToolExecutionError("Intake parser failed.") from exc
