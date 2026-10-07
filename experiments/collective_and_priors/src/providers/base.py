"""Provider-neutral interface used by the fixed eight-action agent loop."""

from __future__ import annotations

from typing import Protocol


class CompletionClient(Protocol):
    def complete(
        self,
        system_message: str,
        user_message: str,
        *,
        json_mode: bool,
        phase: str,
    ) -> str: ...
