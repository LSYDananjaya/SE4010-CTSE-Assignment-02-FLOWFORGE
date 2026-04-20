from __future__ import annotations

import sys

from flowforge.launcher.prompt_toolkit_io import prompt_toolkit_available


def test_prompt_toolkit_availability_returns_boolean() -> None:
    result = prompt_toolkit_available()
    assert isinstance(result, bool)
