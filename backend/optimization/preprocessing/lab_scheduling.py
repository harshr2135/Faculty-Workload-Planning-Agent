"""Shared helpers for lab B1/B2 timetable rules."""

from __future__ import annotations

from backend.core.domain.lab_config import LAB_SUB_BATCHES
from backend.optimization.models.timetable_problem import ScheduleEvent


def section_busy_keys(event: ScheduleEvent, section_index: int) -> tuple[tuple[str, int, str], ...]:
    """Keys used to prevent double-booking a section cohort on the weekly grid.

    - Lab B1 / B2 occupy only their sub-batch (so B1 and B2 may run in parallel).
    - Theory and other non-lab sessions block both sub-batches for the section.
    """
    if event.kind == "lab" and event.lab_sub_batch:
        return ((event.batch_code, section_index, event.lab_sub_batch),)
    return tuple(
        (event.batch_code, section_index, sub_batch) for sub_batch in LAB_SUB_BATCHES
    )


def section_busy_key(event: ScheduleEvent, section_index: int) -> tuple[str, int, str]:
    """Primary section key (first of :func:`section_busy_keys`)."""
    return section_busy_keys(event, section_index)[0]


def sections_schedule_conflict(
    left: ScheduleEvent,
    right: ScheduleEvent,
    *,
    left_sections: tuple[int, ...] | None = None,
    right_sections: tuple[int, ...] | None = None,
) -> bool:
    """True when two events cannot run at the same time for shared section cohorts."""
    left_sections = left_sections if left_sections is not None else left.section_indices
    right_sections = right_sections if right_sections is not None else right.section_indices
    if left.batch_code != right.batch_code:
        return False
    for section_index in set(left_sections) & set(right_sections):
        left_keys = set(section_busy_keys(left, section_index))
        right_keys = set(section_busy_keys(right, section_index))
        if left_keys & right_keys:
            return True
    return False


def fixed_placement_conflicts_with_event(
    event: ScheduleEvent,
    *,
    batch_code: str,
    section_indices: tuple[int, ...],
    treat_as_whole_section: bool = True,
) -> bool:
    """Whether a pre-placed block conflicts with ``event`` on section cohorts."""
    if event.batch_code != batch_code:
        return False
    for section_index in set(event.section_indices) & set(section_indices):
        event_keys = set(section_busy_keys(event, section_index))
        if treat_as_whole_section or event.kind != "lab":
            fixed_keys = {
                (batch_code, section_index, sub_batch) for sub_batch in LAB_SUB_BATCHES
            }
        elif event.lab_sub_batch:
            fixed_keys = {(batch_code, section_index, event.lab_sub_batch)}
        else:
            fixed_keys = set()
        if event_keys & fixed_keys:
            return True
    return False
