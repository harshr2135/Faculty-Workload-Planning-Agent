"""CP-SAT workload allocation solver (Slice 1 — no timetable grid)."""

from __future__ import annotations

import math

from ortools.sat.python import cp_model

from backend.core.domain.policy_config import UNLIMITED_MAX_WEEKLY_HOURS
from backend.optimization.engine.solver_tuning import apply_cpsat_performance
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

        # Max weekly hours per faculty (theory + lab) — skipped when caps are disabled.
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

        # Hard AICTE maximum weekly hours: a faculty member's total load may never exceed
        # the designation cap. May render the problem infeasible if capacity is insufficient.
        for faculty in problem.faculty:
            load = faculty_loads.get(faculty.id)
            if load is None or faculty.max_weekly_hours >= UNLIMITED_MAX_WEEKLY_HOURS:
                continue
            model.Add(load <= int(faculty.max_weekly_hours))

        # ---- Quality objective (dominant): teaching fit + policy softness ----
        # Prefer specialization matches; penalize lab-session overages and one faculty
        # taking multiple sections of the same course.
        quality_terms: list[cp_model.LinearExpr] = []
        for slot in theory_slots:
            for faculty in problem.faculty:
                key = (faculty.id, slot.slot_id)
                if key not in theory_vars:
                    continue
                cost = _assignment_cost(slot, faculty.id, config)
                quality_terms.append(theory_vars[key] * cost)
        for slot in lab_slots:
            for faculty in problem.faculty:
                key = (faculty.id, slot.slot_id)
                if key not in lab_vars:
                    continue
                cost = _assignment_cost(slot, faculty.id, config)
                quality_terms.append(lab_vars[key] * cost)

        for faculty in problem.faculty:
            if faculty.max_lab_sessions is None:
                continue
            lab_terms = [
                lab_vars[(faculty.id, slot.slot_id)]
                for slot in lab_slots
                if (faculty.id, slot.slot_id) in lab_vars
            ]
            if not lab_terms:
                continue
            over_labs = model.NewIntVar(0, len(lab_terms), f"over_labs_{faculty.id}")
            model.Add(over_labs >= sum(lab_terms) - faculty.max_lab_sessions)
            quality_terms.append(over_labs * config.over_max_labs_penalty)

        theory_by_course: dict[int, list[AssignmentSlot]] = {}
        for slot in theory_slots:
            theory_by_course.setdefault(slot.course_id, []).append(slot)
        for course_id, course_slots in theory_by_course.items():
            if len(course_slots) < 2:
                continue
            for faculty in problem.faculty:
                section_terms = [
                    theory_vars[(faculty.id, slot.slot_id)]
                    for slot in course_slots
                    if (faculty.id, slot.slot_id) in theory_vars
                ]
                if len(section_terms) < 2:
                    continue
                duplicate_sections = model.NewIntVar(
                    0, len(section_terms), f"dup_{course_id}_{faculty.id}"
                )
                model.Add(duplicate_sections >= sum(section_terms) - 1)
                quality_terms.append(duplicate_sections * config.duplicate_section_penalty)

        # ---- Balance objective (tie-breaker): keep load proportional to designation caps ----
        balance_terms, balance_upper_bound = self._build_balance_terms(
            model, problem, faculty_loads, config
        )

        # Lexicographic weighting: any 1-unit gain in quality outweighs the entire balance
        # term, so specialization/policy fit is never sacrificed to smooth the distribution.
        quality_weight = balance_upper_bound + 1
        model.Minimize(quality_weight * sum(quality_terms) + sum(balance_terms))

        solver = cp_model.CpSolver()
        apply_cpsat_performance(
            solver,
            config.max_time_seconds,
            stop_after_first_solution=config.stop_after_first_solution,
        )
        status = solver.Solve(model)

        if status not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
            return OptimizationSolution(
                status=_map_status(status),
                objective_value=None,
                messages=[
                    "Solver could not find a feasible assignment. This can happen when the "
                    "AICTE weekly-hour caps leave too little capacity to cover every course. "
                    "Try adding eligible faculty, raising the hour caps, or reducing course load."
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

    @staticmethod
    def _build_balance_terms(
        model: cp_model.CpModel,
        problem: WorkloadProblem,
        faculty_loads: dict[int, cp_model.LinearExpr],
        config: SolverConfig,
    ) -> tuple[list[cp_model.LinearExpr], int]:
        """Build load-balancing objective terms.

        Preferred mode (>=2 faculty with a real cap): proportional balancing. Each faculty's
        hours are scaled into a common utilization space (``load * scale / cap``) so that equal
        scaled loads mean equal utilization — i.e. hours distributed in proportion to caps. The
        L1 spread of these scaled loads around a free target is minimized.

        Fallback (fewer than two real caps): plain peak-load minimization.

        Returns the objective terms plus a provable upper bound on their total, used to weight
        the dominant quality objective above them.
        """
        capped = [
            faculty
            for faculty in problem.faculty
            if faculty.id in faculty_loads
            and 0.0 < faculty.max_weekly_hours < UNLIMITED_MAX_WEEKLY_HOURS
        ]

        if len(capped) < 2:
            if not faculty_loads:
                return [], 0
            max_load = model.NewIntVar(0, 10_000, "max_faculty_load")
            for load in faculty_loads.values():
                model.Add(max_load >= load)
            return [max_load * config.balance_penalty], 10_000 * config.balance_penalty

        caps = {faculty.id: int(round(faculty.max_weekly_hours)) for faculty in capped}
        scale = _utilization_scale(list(caps.values()))
        penalty = config.proportional_balance_penalty

        target = model.NewIntVar(0, scale, "utilization_target")
        balance_terms: list[cp_model.LinearExpr] = []
        for faculty in capped:
            weight = scale // caps[faculty.id]
            scaled_load = faculty_loads[faculty.id] * weight
            deviation = model.NewIntVar(0, scale, f"util_dev_{faculty.id}")
            model.Add(deviation >= scaled_load - target)
            model.Add(deviation >= target - scaled_load)
            balance_terms.append(deviation * penalty)

        return balance_terms, len(capped) * scale * penalty


# Ceiling for the utilization scaling factor. The exact least-common-multiple of the caps
# is used when small (department caps are a handful of small integers); if a pathological
# set of caps produces a very large LCM, we clamp to keep objective coefficients bounded,
# accepting a tiny proportional rounding error.
_UTILIZATION_SCALE_CEILING = 50_000


def _utilization_scale(caps: list[int]) -> int:
    """Common scaling factor so ``load * scale / cap`` is an integer utilization measure."""
    distinct = sorted({cap for cap in caps if cap > 0})
    if not distinct:
        return 1
    scale = math.lcm(*distinct)
    return min(scale, _UTILIZATION_SCALE_CEILING)


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
                requires_lecture_hall=slot.requires_lecture_hall,
                lab_sub_batch=slot.lab_sub_batch,
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
                requires_lecture_hall=slot.requires_lecture_hall,
                lab_sub_batch=slot.lab_sub_batch,
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
