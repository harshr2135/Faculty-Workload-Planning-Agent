"""Phase 2: greedy room assignment after time slots are fixed."""

from __future__ import annotations

from dataclasses import dataclass

from backend.optimization.models.timetable_problem import (
    PeriodInfo,
    RoomInput,
    RoomKind,
    ScheduleEvent,
    TimetableProblem,
)
from backend.optimization.models.timetable_solution import TimetableEntry
from backend.optimization.preprocessing.period_utils import period_window_label


@dataclass(frozen=True)
class TimeSlotAssignment:
    event_index: int
    day: str
    period_block: tuple[int, ...]


def assign_rooms_greedy(
    problem: TimetableProblem,
    assignments: list[TimeSlotAssignment],
    period_lookup: dict[int, PeriodInfo],
) -> list[TimetableEntry] | None:
    """Pick the first available room of the correct type for each timed event."""
    occupied: set[tuple[str, int, str, int]] = set()
    for fixed in problem.fixed_placements:
        room_kind = _room_kind_for_id(problem, fixed.room_id)
        if room_kind is None:
            continue
        for period_number in fixed.period_block:
            occupied.add((fixed.day, period_number, room_kind, fixed.room_id))

    ordered = sorted(
        assignments,
        key=lambda row: (
            row.day,
            row.period_block[0],
            problem.events[row.event_index].batch_code,
            problem.events[row.event_index].course_code,
            row.event_index,
        ),
    )

    entries: list[TimetableEntry] = []
    for assignment in ordered:
        event = problem.events[assignment.event_index]
        rooms = _rooms_for_kind(problem, event.room_kind)
        chosen: RoomInput | None = None
        for room in rooms:
            if _room_free(room, assignment.day, assignment.period_block, occupied):
                chosen = room
                break
        if chosen is None:
            return None

        for period_number in assignment.period_block:
            occupied.add((assignment.day, period_number, chosen.kind.value, chosen.id))

        first = period_lookup[assignment.period_block[0]]
        last = period_lookup[assignment.period_block[-1]]
        entries.append(
            TimetableEntry(
                event_id=event.event_id,
                slot_id=event.slot_id,
                batch_code=event.batch_code,
                course_code=event.course_code,
                course_name=event.course_name,
                course_type=event.course_type,
                kind=event.kind,
                section_indices=list(event.section_indices),
                faculty_ids=list(event.faculty_ids),
                faculty_names=list(event.faculty_names),
                day=assignment.day,
                period_numbers=list(assignment.period_block),
                period_label=period_window_label(assignment.period_block),
                room_type=chosen.kind.value,
                room_name=chosen.name,
                start_time=first.start_time,
                end_time=last.end_time,
            )
        )

    day_order = {day: index for index, day in enumerate(problem.working_days)}
    entries.sort(
        key=lambda row: (
            day_order.get(row.day, 99),
            row.period_numbers[0],
            row.batch_code,
            row.course_code,
        )
    )
    return entries


def _room_free(
    room: RoomInput,
    day: str,
    period_block: tuple[int, ...],
    occupied: set[tuple[str, int, str, int]],
) -> bool:
    return all(
        (day, period_number, room.kind.value, room.id) not in occupied
        for period_number in period_block
    )


def _room_kind_for_id(problem: TimetableProblem, room_id: int) -> str | None:
    for pool in (problem.classrooms, problem.lecture_halls, problem.laboratories):
        for room in pool:
            if room.id == room_id:
                return room.kind.value
    return None


def _rooms_for_kind(problem: TimetableProblem, kind: RoomKind) -> list[RoomInput]:
    if kind == RoomKind.LECTURE_HALL:
        return list(problem.lecture_halls)
    if kind == RoomKind.LABORATORY:
        return list(problem.laboratories)
    return list(problem.classrooms)
