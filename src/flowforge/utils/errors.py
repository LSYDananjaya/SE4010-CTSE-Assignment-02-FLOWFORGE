from __future__ import annotations


class FlowForgeError(Exception):
    """Base exception for FlowForge runtime failures."""


class ToolExecutionError(FlowForgeError):
    """Raised when a deterministic tool fails."""
