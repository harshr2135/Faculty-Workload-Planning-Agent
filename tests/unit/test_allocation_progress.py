"""Unit tests for allocation run progress helpers."""

from backend.services.allocation_progress import (
    RUN_TOTAL_STEPS,
    initial_progress_payload,
    progress_from_payload,
)


def test_initial_progress_payload() -> None:
    payload = initial_progress_payload(batch_codes=["2023-27", "2024-28"])
    assert payload["run_state"] == "running"
    assert payload["progress"]["step"] == 1
    assert payload["progress"]["total_steps"] == RUN_TOTAL_STEPS
    assert payload["progress"]["percent"] == 5
    assert "started_at" in payload


def test_progress_from_payload() -> None:
    payload = initial_progress_payload(batch_codes=["2023-27"])
    progress = progress_from_payload(payload)
    assert progress is not None
    assert progress["phase"] == "preparing"
