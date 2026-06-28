"""Two-phase weekly timetable solver: CP-SAT time slots, then greedy rooms."""

from __future__ import annotations

from dataclasses import dataclass

from ortools.sat.python import cp_model

from backend.optimization.engine.room_assigner import TimeSlotAssignment, assign_rooms_greedy
from backend.optimization.engine.solver_tuning import apply_cpsat_performance
from backend.optimization.models.solution import SolverStatus
from backend.optimization.models.timetable_problem import (
    PeriodInfo,
    RoomKind,
    ScheduleEvent,
    TimetableProblem,
    TimetableSolverConfig,
)
from backend.optimization.models.timetable_solution import TimetableSolution


@dataclass(frozen=True)
class _TimeSlot:
    day: str
    period_block: tuple[int, ...]


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
        slots_by_event: list[list[_TimeSlot]] = []
        for event in problem.events:
            slots = _valid_time_slots(problem, event)
            if not slots:
                return TimetableSolution(
                    status=SolverStatus.INFEASIBLE,
                    messages=[
                        f"No valid time slot for {event.course_code} ({event.event_id}); "
                        "check working days or lab duration."
                    ],
                )
            slots_by_event.append(slots)

        time_result = self._solve_time_slots(problem, slots_by_event, config)
        if time_result.status not in (SolverStatus.OPTIMAL, SolverStatus.FEASIBLE):
            return TimetableSolution(
                status=time_result.status,
                messages=time_result.messages
                or ["Timetable times could not be scheduled without conflicts."],
            )

        room_entries = assign_rooms_greedy(problem, time_result.assignments, period_lookup)
        if room_entries is None:
            return TimetableSolution(
                status=SolverStatus.INFEASIBLE,
                messages=[
                    "Time slots were found but rooms could not be assigned without overlap. "
                    "Add more classrooms, laboratories, or lecture halls."
                ],
            )

        return TimetableSolution(
            status=SolverStatus.FEASIBLE if config.stop_after_first_solution else time_result.status,
            entries=room_entries,
            messages=[
                "First feasible weekly timetable for all batches (time slots + room assignment)."
                if config.stop_after_first_solution
                else "Phase 1: weekly time slots scheduled. Phase 2: rooms assigned greedily."
            ],
        )

    def _solve_time_slots(
        self,
        problem: TimetableProblem,
        slots_by_event: list[list[_TimeSlot]],
        config: TimetableSolverConfig,
    ) -> _TimeSlotSolveResult:
        model = cp_model.CpModel()
        choice_vars: list[list[cp_model.IntVar]] = []
        for event_index, slots in enumerate(slots_by_event):
            row = [
                model.NewBoolVar(f"time_{event_index}_{slot_index}")
                for slot_index in range(len(slots))
            ]
            model.AddExactlyOne(row)
            choice_vars.append(row)

        _add_time_conflict_constraints(
            model,
            problem.events,
            slots_by_event,
            choice_vars,
        )
        _add_room_capacity_constraints(model, problem, slots_by_event, choice_vars)
        _add_spread_constraints(model, problem, slots_by_event, choice_vars)

        # No objective when we only need the first feasible timetable (faster search).
        if not config.stop_after_first_solution:
            objective_terms: list[cp_model.LinearExpr] = []
            day_order = {day: index for index, day in enumerate(problem.working_days)}
            for event_index, slots in enumerate(slots_by_event):
                for slot_index, slot in enumerate(slots):
                    cost = day_order[slot.day] * 100 + slot.period_block[0] * 10
                    objective_terms.append(choice_vars[event_index][slot_index] * cost)
            model.Minimize(sum(objective_terms))

        solver = cp_model.CpSolver()
        apply_cpsat_performance(
            solver,
            config.max_time_seconds,
            stop_after_first_solution=config.stop_after_first_solution,
            num_search_workers=config.num_search_workers,
        )
        status = solver.Solve(model)

        if status not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
            return _TimeSlotSolveResult(
                status=_map_status(status),
                assignments=[],
                messages=[
                    "Timetable times could not be scheduled without conflicts. "
                    "Try fewer concurrent courses or additional faculty."
                ],
            )

        assignments: list[TimeSlotAssignment] = []
        for event_index, slots in enumerate(slots_by_event):
            for slot_index, slot in enumerate(slots):
                if solver.Value(choice_vars[event_index][slot_index]) != 1:
                    continue
                assignments.append(
                    TimeSlotAssignment(
                        event_index=event_index,
                        day=slot.day,
                        period_block=slot.period_block,
                    )
                )
                break

        return _TimeSlotSolveResult(
            status=(
                SolverStatus.FEASIBLE
                if config.stop_after_first_solution
                else _map_status(status)
            ),
            assignments=assignments,
        )


@dataclass
class _TimeSlotSolveResult:
    status: SolverStatus
    assignments: list[TimeSlotAssignment]
    messages: list[str] | None = None


def _valid_time_slots(problem: TimetableProblem, event: ScheduleEvent) -> list[_TimeSlot]:
    blocks = problem.consecutive_blocks.get(event.duration_periods, ())
    if not blocks:
        return []

    period_lookup = {info.period_number: info for info in problem.period_info}
    slots: list[_TimeSlot] = []
    days = event.working_days or problem.working_days
    for day in days:
        for block in blocks:
            if not all(period_number in period_lookup for period_number in block):
                continue
            slot = _TimeSlot(day=day, period_block=block)
            if not _conflicts_with_fixed_time(event, slot, problem.fixed_placements):
                slots.append(slot)
    return slots


def _conflicts_with_fixed_time(
    event: ScheduleEvent,
    slot: _TimeSlot,
    fixed_placements: tuple,
) -> bool:
    for fixed in fixed_placements:
        if slot.day != fixed.day:
            continue
        if not set(slot.period_block) & set(fixed.period_block):
            continue
        if set(event.faculty_ids) & set(fixed.faculty_ids):
            return True
        if (
            event.batch_code == fixed.batch_code
            and set(event.section_indices) & set(fixed.section_indices)
        ):
            return True
    return False


def _add_time_conflict_constraints(
    model: cp_model.CpModel,
    events: tuple[ScheduleEvent, ...],
    slots_by_event: list[list[_TimeSlot]],
    choice_vars: list[list[cp_model.IntVar]],
) -> None:
    """At most one event per faculty or section in each day+period cell."""
    cell_literals: dict[tuple[str, int], list[tuple[int, int]]] = {}
    for event_index, slots in enumerate(slots_by_event):
        for slot_index, slot in enumerate(slots):
            for period_number in slot.period_block:
                cell_literals.setdefault((slot.day, period_number), []).append(
                    (event_index, slot_index)
                )

    for (day, period_number), literals in cell_literals.items():
        if len(literals) < 2:
            continue

        faculty_groups: dict[int, list[cp_model.IntVar]] = {}
        section_groups: dict[tuple[str, int], list[cp_model.IntVar]] = {}
        for event_index, slot_index in literals:
            var = choice_vars[event_index][slot_index]
            event = events[event_index]
            for faculty_id in event.faculty_ids:
                faculty_groups.setdefault(faculty_id, []).append(var)
            for section_index in event.section_indices:
                section_groups.setdefault((event.batch_code, section_index), []).append(var)

        for group in faculty_groups.values():
            if len(group) > 1:
                model.AddAtMostOne(group)
        for group in section_groups.values():
            if len(group) > 1:
                model.AddAtMostOne(group)


def _add_room_capacity_constraints(
    model: cp_model.CpModel,
    problem: TimetableProblem,
    slots_by_event: list[list[_TimeSlot]],
    choice_vars: list[list[cp_model.IntVar]],
) -> None:
    """Ensure each day+period does not exceed available rooms of each kind."""
    room_counts = {
        RoomKind.CLASSROOM: len(problem.classrooms),
        RoomKind.LECTURE_HALL: len(problem.lecture_halls),
        RoomKind.LABORATORY: len(problem.laboratories),
    }
    cell_kind_literals: dict[tuple[str, int, RoomKind], list[cp_model.IntVar]] = {}
    for event_index, slots in enumerate(slots_by_event):
        event = problem.events[event_index]
        for slot_index, slot in enumerate(slots):
            var = choice_vars[event_index][slot_index]
            for period_number in slot.period_block:
                key = (slot.day, period_number, event.room_kind)
                cell_kind_literals.setdefault(key, []).append(var)

    for (day, period_number, room_kind), literals in cell_kind_literals.items():
        capacity = room_counts.get(room_kind, 0)
        if capacity <= 0:
            for var in literals:
                model.Add(var == 0)
            continue
        if len(literals) > capacity:
            model.Add(sum(literals) <= capacity)


def _add_spread_constraints(
    model: cp_model.CpModel,
    problem: TimetableProblem,
    slots_by_event: list[list[_TimeSlot]],
    choice_vars: list[list[cp_model.IntVar]],
) -> None:
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
        day_literals: dict[str, list[cp_model.IntVar]] = {}
        for event_index in indices:
            for slot_index, slot in enumerate(slots_by_event[event_index]):
                day_literals.setdefault(slot.day, []).append(choice_vars[event_index][slot_index])
        for group in day_literals.values():
            if len(group) > 1:
                model.AddAtMostOne(group)


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
