"""CP-SAT workload allocation solver (Slice 1 — no timetable grid)."""

from __future__ import annotations

from ortools.sat.python import cp_model

from backend.optimization.models.problem_definition import AssignmentSlot, SlotKind, SolverConfig, WorkloadProblem
from backend.optimization.models.solution import (
    FacultyWorkloadSummary,
    OptimizationSolution,
    PolicyViolation,
    SlotAssignment,
    SolverStatus,
)
from backend.optimization.postprocessing.validator import validate_solution


class WorkloadCpsatSolver:
    def solve(
        self,
        problem: WorkloadProblem,
        config: SolverConfig | None = None,
    ) -> OptimizationSolution:
        config = config or SolverConfig()
        faculty_by_id = {member.id: member for member in problem.faculty}
        theory_slots = [slot for slot in problem.slots if slot.kind == SlotKind.THEORY]
        lab_slots = [slot for slot in problem.slots if slot.kind == SlotKind.LAB]

        if not problem.faculty:
            return OptimizationSolution(
                status=SolverStatus.INFEASIBLE,
                objective_value=None,
                messages=["No faculty available for allocation."],
            )
        if not problem.slots:
            return OptimizationSolution(
                status=SolverStatus.INFEASIBLE,
                objective_value=None,
                messages=["No teaching slots generated for this batch and semester."],
            )

        for slot in problem.slots:
            if not slot.eligible_faculty_ids:
                return OptimizationSolution(
                    status=SolverStatus.INFEASIBLE,
                    objective_value=None,
                    violations=[
                        PolicyViolation(
                            code="no_eligible_faculty",
                            message=(
                                f"No eligible faculty for {slot.course_code} "
                                f"({slot.kind.value}); specialization fallback pool is empty."
                            ),
                            course_code=slot.course_code,
                        )
                    ],
                )

        model = cp_model.CpModel()
        theory_vars: dict[tuple[int, str], cp_model.IntVar] = {}
        lab_vars: dict[tuple[int, str], cp_model.IntVar] = {}

        for slot in theory_slots:
            for faculty in problem.faculty:
                if faculty.id in slot.eligible_faculty_ids:
                    theory_vars[(faculty.id, slot.slot_id)] = model.NewBoolVar(
                        f"t_{faculty.id}_{slot.slot_id}"
                    )

        for slot in lab_slots:
            for faculty in problem.faculty:
                if faculty.id in slot.eligible_faculty_ids:
                    lab_vars[(faculty.id, slot.slot_id)] = model.NewBoolVar(
                        f"l_{faculty.id}_{slot.slot_id}"
                    )

        # Coverage: exactly one faculty per theory slot.
        for slot in theory_slots:
            candidates = [
                theory_vars[(faculty.id, slot.slot_id)]
                for faculty in problem.faculty
                if (faculty.id, slot.slot_id) in theory_vars
            ]
            model.Add(sum(candidates) == 1)

        # Coverage: exactly N faculty per lab slot.
        for slot in lab_slots:
            candidates = [
                lab_vars[(faculty.id, slot.slot_id)]
                for faculty in problem.faculty
                if (faculty.id, slot.slot_id) in lab_vars
            ]
            model.Add(sum(candidates) == problem.lab_faculty_per_session)

        # Max weekly hours per faculty (theory + lab).
        faculty_loads: dict[int, cp_model.LinearExpr] = {}
        for faculty in problem.faculty:
            terms: list[cp_model.LinearExpr] = []
            for slot in theory_slots:
                key = (faculty.id, slot.slot_id)
                if key in theory_vars:
                    terms.append(theory_vars[key] * slot.weekly_hours)
            for slot in lab_slots:
                key = (faculty.id, slot.slot_id)
                if key in lab_vars:
                    terms.append(lab_vars[key] * slot.weekly_hours)
            if terms:
                faculty_loads[faculty.id] = sum(terms)
                max_hours = int(faculty.max_weekly_hours * config.hours_scale)
                model.Add(faculty_loads[faculty.id] <= max_hours)

        # Objective: prefer specialization matches, then balance load.
        objective_terms: list[cp_model.LinearExpr] = []
        for slot in theory_slots:
            for faculty in problem.faculty:
                key = (faculty.id, slot.slot_id)
                if key not in theory_vars:
                    continue
                cost = _assignment_cost(slot, faculty.id, config)
                objective_terms.append(theory_vars[key] * cost)
        for slot in lab_slots:
            for faculty in problem.faculty:
                key = (faculty.id, slot.slot_id)
                if key not in lab_vars:
                    continue
                cost = _assignment_cost(slot, faculty.id, config)
                objective_terms.append(lab_vars[key] * cost)

        if faculty_loads:
            max_load = model.NewIntVar(0, 10_000, "max_faculty_load")
            for load in faculty_loads.values():
                model.Add(max_load >= load)
            objective_terms.append(max_load * config.balance_penalty)

        model.Minimize(sum(objective_terms))

        solver = cp_model.CpSolver()
        solver.parameters.max_time_in_seconds = config.max_time_seconds
        status = solver.Solve(model)

        if status not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
            return OptimizationSolution(
                status=_map_status(status),
                objective_value=None,
                messages=[
                    "Solver could not find a feasible assignment. "
                    "Try relaxing constraints, adding faculty, or reviewing course load."
                ],
            )

        assignments = _extract_assignments(
            problem,
            theory_slots,
            lab_slots,
            theory_vars,
            lab_vars,
            faculty_by_id,
            solver,
        )
        summaries = _build_summaries(problem, assignments, faculty_by_id)
        solution = OptimizationSolution(
            status=_map_status(status),
            objective_value=int(solver.ObjectiveValue()),
            assignments=assignments,
            faculty_summaries=summaries,
        )
        solution.violations = validate_solution(problem, solution)
        return solution


def _assignment_cost(slot: AssignmentSlot, faculty_id: int, config: SolverConfig) -> int:
    if faculty_id in slot.specialization_matched_ids:
        return 0
    if slot.fallback_required:
        return config.fallback_penalty
    return config.mismatch_penalty


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


def _extract_assignments(
    problem: WorkloadProblem,
    theory_slots: list[AssignmentSlot],
    lab_slots: list[AssignmentSlot],
    theory_vars: dict[tuple[int, str], cp_model.IntVar],
    lab_vars: dict[tuple[int, str], cp_model.IntVar],
    faculty_by_id: dict[int, object],
    solver: cp_model.CpSolver,
) -> list[SlotAssignment]:
    assignments: list[SlotAssignment] = []

    for slot in theory_slots:
        assigned_ids = [
            faculty_id
            for faculty_id in faculty_by_id
            if (faculty_id, slot.slot_id) in theory_vars
            and solver.Value(theory_vars[(faculty_id, slot.slot_id)]) == 1
        ]
        assignments.append(
            SlotAssignment(
                slot_id=slot.slot_id,
                batch_code=slot.batch_code,
                working_days=slot.working_days,
                course_id=slot.course_id,
                course_code=slot.course_code,
                course_name=slot.course_name,
                course_type=slot.course_type,
                kind=slot.kind.value,
                section_indices=list(slot.section_indices),
                weekly_hours=slot.weekly_hours,
                faculty_ids=assigned_ids,
                faculty_names=[faculty_by_id[fid].full_name for fid in assigned_ids],
            )
        )

    for slot in lab_slots:
        assigned_ids = [
            faculty_id
            for faculty_id in faculty_by_id
            if (faculty_id, slot.slot_id) in lab_vars
            and solver.Value(lab_vars[(faculty_id, slot.slot_id)]) == 1
        ]
        assignments.append(
            SlotAssignment(
                slot_id=slot.slot_id,
                batch_code=slot.batch_code,
                working_days=slot.working_days,
                course_id=slot.course_id,
                course_code=slot.course_code,
                course_name=slot.course_name,
                course_type=slot.course_type,
                kind=slot.kind.value,
                section_indices=list(slot.section_indices),
                weekly_hours=slot.weekly_hours,
                faculty_ids=assigned_ids,
                faculty_names=[faculty_by_id[fid].full_name for fid in assigned_ids],
            )
        )

    return assignments


def _build_summaries(
    problem: WorkloadProblem,
    assignments: list[SlotAssignment],
    faculty_by_id: dict[int, object],
) -> list[FacultyWorkloadSummary]:
    summaries: list[FacultyWorkloadSummary] = []
    for faculty in problem.faculty:
        theory_hours = 0
        lab_hours = 0
        theory_courses: set[int] = set()
        lab_courses: set[int] = set()
        lab_sessions = 0

        for assignment in assignments:
            if faculty.id not in assignment.faculty_ids:
                continue
            if assignment.kind == SlotKind.THEORY.value:
                theory_hours += assignment.weekly_hours
                theory_courses.add(assignment.course_id)
            else:
                lab_hours += assignment.weekly_hours
                lab_courses.add(assignment.course_id)
                lab_sessions += 1

        summaries.append(
            FacultyWorkloadSummary(
                faculty_id=faculty.id,
                full_name=faculty.full_name,
                designation_key=faculty.designation_key,
                theory_weekly_hours=theory_hours,
                lab_weekly_hours=lab_hours,
                total_weekly_hours=theory_hours + lab_hours,
                theory_course_count=len(theory_courses),
                lab_course_count=len(lab_courses),
                lab_session_count=lab_sessions,
            )
        )
    return summaries
