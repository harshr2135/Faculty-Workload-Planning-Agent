"""CP-SAT weekly timetable grid solver (Slice 2)."""

from __future__ import annotations

from dataclasses import dataclass

from ortools.sat.python import cp_model

from backend.optimization.models.solution import SolverStatus
from backend.optimization.models.timetable_problem import (
    PeriodInfo,
    RoomInput,
    RoomKind,
    ScheduleEvent,
    TimetableProblem,
    TimetableSolverConfig,
)
from backend.optimization.models.timetable_solution import TimetableEntry, TimetableSolution
from backend.optimization.preprocessing.period_utils import period_window_label


@dataclass(frozen=True)
class _Placement:
    day: str
    period_block: tuple[int, ...]
    room: RoomInput


class TimetableCpsatSolver:
    def solve(
        self,
        problem: TimetableProblem,
        config: TimetableSolverConfig | None = None,
    ) -> TimetableSolution:
        config = config or TimetableSolverConfig()
        if not problem.events:
            return TimetableSolution(
                status=SolverStatus.INFEASIBLE,
                messages=["No schedule events to place on the timetable."],
            )

        period_lookup = {info.period_number: info for info in problem.period_info}
        placements_by_event: list[list[_Placement]] = []
        for event in problem.events:
            placements = _valid_placements(problem, event)
            if not placements:
                return TimetableSolution(
                    status=SolverStatus.INFEASIBLE,
                    messages=[
                        f"No valid timetable placement for {event.course_code} "
                        f"({event.event_id}); check rooms or lab duration."
                    ],
                )
            placements_by_event.append(placements)

        model = cp_model.CpModel()
        choice_vars: list[list[cp_model.IntVar]] = []
        for event_index, placements in enumerate(placements_by_event):
            row = [
                model.NewBoolVar(f"place_{event_index}_{placement_index}")
                for placement_index in range(len(placements))
            ]
            model.Add(sum(row) == 1)
            choice_vars.append(row)

        # Resource conflicts grouped by day+period cell (faculty, room, sections).
        cell_literals: dict[tuple[str, int], list[tuple[int, int]]] = {}
        for event_index, placements in enumerate(placements_by_event):
            for placement_index, placement in enumerate(placements):
                for period_number in placement.period_block:
                    cell_literals.setdefault((placement.day, period_number), []).append(
                        (event_index, placement_index)
                    )

        for literals in cell_literals.values():
            if len(literals) < 2:
                continue
            for left_pos in range(len(literals)):
                left_event_index, left_placement_index = literals[left_pos]
                left_event = problem.events[left_event_index]
                left_placement = placements_by_event[left_event_index][left_placement_index]
                for right_pos in range(left_pos + 1, len(literals)):
                    right_event_index, right_placement_index = literals[right_pos]
                    right_event = problem.events[right_event_index]
                    right_placement = placements_by_event[right_event_index][right_placement_index]
                    if not _placements_conflict(
                        left_event,
                        left_placement,
                        right_event,
                        right_placement,
                    ):
                        continue
                    model.Add(
                        choice_vars[left_event_index][left_placement_index]
                        + choice_vars[right_event_index][right_placement_index]
                        <= 1
                    )

        # Spread weekly theory sessions across different working days when there are
        # enough days; 4th-year (Thu–Fri only) courses with 3 lectures/week may share a day.
        slot_to_event_indices: dict[str, list[int]] = {}
        for index, event in enumerate(problem.events):
            if event.kind == "theory" and event.duration_periods == 1:
                slot_to_event_indices.setdefault(event.slot_id, []).append(index)

        for indices in slot_to_event_indices.values():
            if len(indices) <= 1:
                continue
            sample_event = problem.events[indices[0]]
            working_day_count = len(sample_event.working_days or problem.working_days)
            if len(indices) > working_day_count:
                continue
            day_literals: dict[str, list[tuple[int, int]]] = {}
            for event_index in indices:
                for placement_index, placement in enumerate(placements_by_event[event_index]):
                    day_literals.setdefault(placement.day, []).append(
                        (event_index, placement_index)
                    )
            for literals in day_literals.values():
                if len(literals) <= 1:
                    continue
                model.Add(
                    sum(choice_vars[event_index][placement_index] for event_index, placement_index in literals)
                    <= 1
                )

        # Prefer earlier days/periods and lower-index rooms (deterministic tie-break).
        objective_terms: list[cp_model.LinearExpr] = []
        day_order = {day: index for index, day in enumerate(problem.working_days)}
        for event_index, placements in enumerate(placements_by_event):
            for placement_index, placement in enumerate(placements):
                period_start = placement.period_block[0]
                cost = day_order[placement.day] * 100 + period_start * 10 + placement.room.id
                objective_terms.append(choice_vars[event_index][placement_index] * cost)
        model.Minimize(sum(objective_terms))

        solver = cp_model.CpSolver()
        solver.parameters.max_time_in_seconds = config.max_time_seconds
        status = solver.Solve(model)

        if status not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
            return TimetableSolution(
                status=_map_status(status),
                messages=[
                    "Timetable could not be scheduled without conflicts. "
                    "Try fewer concurrent courses or additional rooms."
                ],
            )

        entries = _extract_entries(
            problem.events,
            problem.working_days,
            placements_by_event,
            choice_vars,
            period_lookup,
            solver,
        )
        return TimetableSolution(
            status=_map_status(status),
            entries=entries,
            messages=["Weekly grid fixed for the semester; same pattern repeats each week."],
        )


def _valid_placements(problem: TimetableProblem, event: ScheduleEvent) -> list[_Placement]:
    blocks = problem.consecutive_blocks.get(event.duration_periods, ())
    rooms = _rooms_for_kind(problem, event.room_kind)
    if not blocks or not rooms:
        return []

    placements: list[_Placement] = []
    days = event.working_days or problem.working_days
    for day in days:
        for block in blocks:
            for room in rooms:
                placements.append(_Placement(day=day, period_block=block, room=room))
    return placements


def _rooms_for_kind(problem: TimetableProblem, kind: RoomKind) -> list[RoomInput]:
    if kind == RoomKind.LECTURE_HALL:
        return list(problem.lecture_halls)
    if kind == RoomKind.LABORATORY:
        return list(problem.laboratories)
    return list(problem.classrooms)


def _placements_conflict(
    left_event: ScheduleEvent,
    left: _Placement,
    right_event: ScheduleEvent,
    right: _Placement,
) -> bool:
    if not _placements_overlap(left, right):
        return False
    if left.room.id == right.room.id:
        return True
    if set(left_event.faculty_ids) & set(right_event.faculty_ids):
        return True
    if (
        left_event.batch_code == right_event.batch_code
        and set(left_event.section_indices) & set(right_event.section_indices)
    ):
        return True
    return False


def _placements_overlap(left: _Placement, right: _Placement) -> bool:
    if left.day != right.day:
        return False
    return bool(set(left.period_block) & set(right.period_block))


def _map_status(status: int) -> SolverStatus:
    if status == cp_model.OPTIMAL:
        return SolverStatus.OPTIMAL
    if status == cp_model.FEASIBLE:
        return SolverStatus.FEASIBLE
    if status == cp_model.INFEASIBLE:
        return SolverStatus.INFEASIBLE
    if status == cp_model.UNKNOWN:
        return SolverStatus.UNKNOWN
    return SolverStatus.TIMEOUT


def _extract_entries(
    events: tuple[ScheduleEvent, ...],
    working_days: tuple[str, ...],
    placements_by_event: list[list[_Placement]],
    choice_vars: list[list[cp_model.IntVar]],
    period_lookup: dict[int, PeriodInfo],
    solver: cp_model.CpSolver,
) -> list[TimetableEntry]:
    entries: list[TimetableEntry] = []
    for event_index, event in enumerate(events):
        for placement_index, placement in enumerate(placements_by_event[event_index]):
            if solver.Value(choice_vars[event_index][placement_index]) != 1:
                continue
            first = period_lookup[placement.period_block[0]]
            last = period_lookup[placement.period_block[-1]]
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
                    day=placement.day,
                    period_numbers=list(placement.period_block),
                    period_label=period_window_label(placement.period_block),
                    room_type=placement.room.kind.value,
                    room_name=placement.room.name,
                    start_time=first.start_time,
                    end_time=last.end_time,
                )
            )
            break
    day_order = {day: index for index, day in enumerate(working_days)}
    entries.sort(
        key=lambda row: (day_order.get(row.day, 99), row.period_numbers[0], row.course_code)
    )
    return entries
