"""Addendum 07 contentless transient-request retries and append-only ledger notes."""

from __future__ import annotations

import json
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, TypeVar

import anthropic

T = TypeVar("T")
BACKOFF_SECONDS = (2, 4, 8, 16, 32)


class RetryExhausted(RuntimeError):
    """The initial request and all five identical resends failed transiently."""


def is_transient(exc: Exception) -> bool:
    if isinstance(exc, anthropic.APIConnectionError):
        return True
    if isinstance(exc, anthropic.APIStatusError):
        return exc.status_code == 429 or 500 <= exc.status_code <= 599
    return False


def append_ledger_note(path: Path, note: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(note, sort_keys=True) + "\n")


def call_with_transient_retries(
    request: Callable[[], T],
    *,
    notes_path: Path,
    request_id: str,
    sleep: Callable[[float], None] = time.sleep,
) -> T:
    """Retry only a failed, contentless request; never alter its arguments."""
    for attempt_number in range(1, len(BACKOFF_SECONDS) + 2):
        try:
            return request()
        except Exception as exc:
            if not is_transient(exc):
                raise
            if attempt_number > len(BACKOFF_SECONDS):
                append_ledger_note(notes_path, {
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "request_id": request_id,
                    "event": "retry_exhausted",
                    "error_class": type(exc).__name__,
                    "attempt_number": attempt_number,
                })
                raise RetryExhausted(
                    f"{request_id}: {type(exc).__name__} after {attempt_number} total attempts"
                ) from exc
            delay = BACKOFF_SECONDS[attempt_number - 1]
            append_ledger_note(notes_path, {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "request_id": request_id,
                "event": "retry",
                "error_class": type(exc).__name__,
                "attempt_number": attempt_number + 1,
                "backoff_seconds": delay,
            })
            sleep(delay)
    raise AssertionError("unreachable retry state")
