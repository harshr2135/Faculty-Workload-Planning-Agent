"""PEC pool parallel scheduling helpers."""

from __future__ import annotations

from backend.core.domain.pec_config import pec_parallel_time_key, pec_pool_label
from backend.optimization.models.timetable_problem import ScheduleEvent


def pec_events_share_parallel_pool(left: ScheduleEvent, right: ScheduleEvent) -> bool:
    """True when two theory events belong to the same PEC pool in the same batch."""
    if left.kind != "theory" or right.kind != "theory":
        return False
    left_pool = pec_pool_label(left.course_type)
    right_pool = pec_pool_label(right.course_type)
    return (
        left_pool is not None
        and left_pool == right_pool
        and left.batch_code == right.batch_code
    )


def pec_parallel_group_key(event: ScheduleEvent) -> tuple[str, str, int] | None:
    if event.kind != "theory":
        return None
    return pec_parallel_time_key(event.batch_code, event.course_type, event.session_index)
