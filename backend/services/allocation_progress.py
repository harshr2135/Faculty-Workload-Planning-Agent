"""Phase-based progress tracking for background allocation runs."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any

from sqlalchemy.ext.asyncio import AsyncSession

if TYPE_CHECKING:
    from backend.models import AllocationRun

RUN_TOTAL_STEPS = 6


def initial_progress_payload(
    *,
    batch_codes: list[str],
    existing: dict[str, Any] | None = None,
) -> dict[str, Any]:
    payload = dict(existing or {})
    payload["run_state"] = "running"
    payload["batch_codes"] = batch_codes
    payload.setdefault("started_at", datetime.now(timezone.utc).isoformat())
    payload["progress"] = _progress_dict(
        phase="preparing",
        label="Preparing courses, faculty, and rooms…",
        percent=5,
        step=1,
    )
    return payload


def progress_from_payload(payload: dict[str, Any] | None) -> dict[str, Any] | None:
    raw = (payload or {}).get("progress")
    if not isinstance(raw, dict):
        return None
    return raw


async def update_run_progress(
    session: AsyncSession,
    run: AllocationRun,
    *,
    phase: str,
    label: str,
    percent: int,
    step: int,
) -> None:
    payload = dict(run.solution or {})
    payload["run_state"] = "running"
    payload["progress"] = _progress_dict(
        phase=phase,
        label=label,
        percent=percent,
        step=step,
    )
    run.solution = payload
    await session.commit()


def _progress_dict(
    *,
    phase: str,
    label: str,
    percent: int,
    step: int,
) -> dict[str, Any]:
    return {
        "phase": phase,
        "label": label,
        "percent": min(100, max(0, percent)),
        "step": min(step, RUN_TOTAL_STEPS),
        "total_steps": RUN_TOTAL_STEPS,
    }
