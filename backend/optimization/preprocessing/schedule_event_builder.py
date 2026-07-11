"""Build weekly grid events from workload assignments."""

from __future__ import annotations

from backend.core.domain.course_type_config import requires_room_allocation
from backend.optimization.models.solution import SlotAssignment
from backend.optimization.models.timetable_problem import RoomKind, ScheduleEvent
from backend.optimization.preprocessing.period_utils import consecutive_teaching_blocks


def build_schedule_events(assignments: list[SlotAssignment]) -> list[ScheduleEvent]:
    events: list[ScheduleEvent] = []

    for assignment in assignments:
        room_kind = _room_kind_for_assignment(assignment)

        if assignment.kind == "theory":
            session_count = max(1, assignment.weekly_hours)
            for session_index in range(1, session_count + 1):
                events.append(
                    ScheduleEvent(
                        event_id=f"{assignment.slot_id}-W{session_index}",
                        slot_id=assignment.slot_id,
                        batch_code=assignment.batch_code,
                        working_days=assignment.working_days,
                        course_id=assignment.course_id,
                        course_code=assignment.course_code,
                        course_name=assignment.course_name,
                        course_type=assignment.course_type,
                        kind=assignment.kind,
                        section_indices=tuple(assignment.section_indices),
                        lab_sub_batch=assignment.lab_sub_batch,
                        faculty_ids=tuple(assignment.faculty_ids),
                        faculty_names=tuple(assignment.faculty_names),
                        duration_periods=1,
                        room_kind=room_kind,
                        session_index=session_index,
                    )
                )
        else:
            duration = max(1, assignment.weekly_hours)
            events.append(
                ScheduleEvent(
                    event_id=f"{assignment.slot_id}-LAB",
                    slot_id=assignment.slot_id,
                    batch_code=assignment.batch_code,
                    working_days=assignment.working_days,
                    course_id=assignment.course_id,
                    course_code=assignment.course_code,
                    course_name=assignment.course_name,
                    course_type=assignment.course_type,
                    kind=assignment.kind,
                    section_indices=tuple(assignment.section_indices),
                    lab_sub_batch=assignment.lab_sub_batch,
                    faculty_ids=tuple(assignment.faculty_ids),
                    faculty_names=tuple(assignment.faculty_names),
                    duration_periods=duration,
                    room_kind=RoomKind.LABORATORY,
                    session_index=1,
                )
            )

    return events


def build_consecutive_block_index(max_duration: int) -> dict[int, tuple[tuple[int, ...], ...]]:
    return {
        duration: tuple(consecutive_teaching_blocks(duration))
        for duration in range(1, max_duration + 1)
    }


def _room_kind_for_assignment(assignment: SlotAssignment) -> RoomKind:
    if not requires_room_allocation(assignment.course_name):
        return RoomKind.NONE
    if assignment.kind == "lab":
        return RoomKind.LABORATORY
    if assignment.requires_lecture_hall:
        return RoomKind.LECTURE_HALL
    return RoomKind.CLASSROOM
