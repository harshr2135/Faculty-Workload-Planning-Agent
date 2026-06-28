"""Greedy weekly timetable scheduler (no CP-SAT): first free day, period, and room."""

from __future__ import annotations

from backend.optimization.models.solution import SolverStatus
from backend.optimization.models.timetable_problem import (
    PeriodInfo,
    RoomInput,
    RoomKind,
    ScheduleEvent,
    TimetableProblem,
)
from backend.optimization.models.timetable_solution import TimetableEntry, TimetableSolution
from backend.optimization.preprocessing.period_utils import period_window_label


class GreedyTimetableScheduler:
    def schedule(self, problem: TimetableProblem) -> TimetableSolution:
        if not problem.events:
            return TimetableSolution(
                status=SolverStatus.INFEASIBLE,
                messages=["No schedule events to place on the timetable."],
            )

        period_lookup = {info.period_number: info for info in problem.period_info}
        faculty_busy: set[tuple[str, int, int]] = set()
        section_busy: set[tuple[str, int, str, int]] = set()
        room_busy: set[tuple[str, int, str, int]] = set()
        theory_days_by_slot: dict[str, set[str]] = {}

        entries: list[TimetableEntry] = []
        ordered_events = sorted(
            problem.events,
            key=lambda event: (
                event.batch_code,
                event.course_code,
                event.kind,
                event.session_index,
                event.event_id,
            ),
        )

        for event in ordered_events:
            placement = self._first_free_placement(
                problem,
                event,
                period_lookup,
                faculty_busy,
                section_busy,
                room_busy,
                theory_days_by_slot,
            )
            if placement is None:
                return TimetableSolution(
                    status=SolverStatus.INFEASIBLE,
                    messages=[
                        f"Could not place {event.course_code} ({event.event_id}) on the grid. "
                        "Try fewer concurrent courses or additional rooms."
                    ],
                )

            day, period_block, room = placement
            self._occupy(
                event,
                day,
                period_block,
                room,
                faculty_busy,
                section_busy,
                room_busy,
            )
            if event.kind == "theory" and event.duration_periods == 1:
                theory_days_by_slot.setdefault(event.slot_id, set()).add(day)

            first = period_lookup[period_block[0]]
            last = period_lookup[period_block[-1]]
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
                    day=day,
                    period_numbers=list(period_block),
                    period_label=period_window_label(period_block),
                    room_type=room.kind.value,
                    room_name=room.name,
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
        return TimetableSolution(
            status=SolverStatus.FEASIBLE,
            entries=entries,
            messages=["Greedy timetable: first available slot across all batches."],
        )

    def _first_free_placement(
        self,
        problem: TimetableProblem,
        event: ScheduleEvent,
        period_lookup: dict[int, PeriodInfo],
        faculty_busy: set[tuple[str, int, int]],
        section_busy: set[tuple[str, int, str, int]],
        room_busy: set[tuple[str, int, str, int]],
        theory_days_by_slot: dict[str, set[str]],
    ) -> tuple[str, tuple[int, ...], RoomInput] | None:
        blocks = problem.consecutive_blocks.get(event.duration_periods, ())
        rooms = _rooms_for_kind(problem, event.room_kind)
        if not blocks or not rooms:
            return None

        days = list(event.working_days or problem.working_days)
        working_day_count = len(days)
        same_slot_sessions = sum(
            1 for other in problem.events if other.slot_id == event.slot_id
        )
        spread_required = (
            event.kind == "theory"
            and event.duration_periods == 1
            and same_slot_sessions > 1
            and same_slot_sessions <= working_day_count
        )

        for day in days:
            if spread_required and day in theory_days_by_slot.get(event.slot_id, set()):
                continue
            for block in blocks:
                if not all(period in period_lookup for period in block):
                    continue
                if self._has_resource_conflict(
                    event,
                    day,
                    block,
                    faculty_busy,
                    section_busy,
                ):
                    continue
                for room in rooms:
                    if self._room_conflict(day, block, room, room_busy):
                        continue
                    return day, block, room
        return None

    def _has_resource_conflict(
        self,
        event: ScheduleEvent,
        day: str,
        period_block: tuple[int, ...],
        faculty_busy: set[tuple[str, int, int]],
        section_busy: set[tuple[str, int, str, int]],
    ) -> bool:
        for period in period_block:
            for faculty_id in event.faculty_ids:
                if (day, period, faculty_id) in faculty_busy:
                    return True
            for section_index in event.section_indices:
                if (day, period, event.batch_code, section_index) in section_busy:
                    return True
        return False

    def _room_conflict(
        self,
        day: str,
        period_block: tuple[int, ...],
        room: RoomInput,
        room_busy: set[tuple[str, int, str, int]],
    ) -> bool:
        return any(
            (day, period, room.kind.value, room.id) in room_busy for period in period_block
        )

    def _occupy(
        self,
        event: ScheduleEvent,
        day: str,
        period_block: tuple[int, ...],
        room: RoomInput,
        faculty_busy: set[tuple[str, int, int]],
        section_busy: set[tuple[str, int, str, int]],
        room_busy: set[tuple[str, int, str, int]],
    ) -> None:
        for period in period_block:
            for faculty_id in event.faculty_ids:
                faculty_busy.add((day, period, faculty_id))
            for section_index in event.section_indices:
                section_busy.add((day, period, event.batch_code, section_index))
            room_busy.add((day, period, room.kind.value, room.id))


def _rooms_for_kind(problem: TimetableProblem, kind: RoomKind) -> list[RoomInput]:
    if kind == RoomKind.LECTURE_HALL:
        return list(problem.lecture_halls)
    if kind == RoomKind.LABORATORY:
        return list(problem.laboratories)
    return list(problem.classrooms)
