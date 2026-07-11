"""Greedy faculty workload assignment (no CP-SAT)."""

from __future__ import annotations

from backend.optimization.models.problem_definition import AssignmentSlot, SlotKind, WorkloadProblem
from backend.optimization.models.solution import (
    FacultyWorkloadSummary,
    OptimizationSolution,
    PolicyViolation,
    SlotAssignment,
    SolverStatus,
)
from backend.optimization.postprocessing.validator import validate_solution


class GreedyWorkloadAllocator:
    def allocate(self, problem: WorkloadProblem) -> OptimizationSolution:
        faculty_by_id = {member.id: member for member in problem.faculty}
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

        loads: dict[int, int] = {member.id: 0 for member in problem.faculty}
        lab_sessions: dict[int, int] = {member.id: 0 for member in problem.faculty}
        theory_faculty_by_course_batch: dict[tuple[str, int], set[int]] = {}
        assignments: list[SlotAssignment] = []

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
                                f"({slot.kind.value})."
                            ),
                            course_code=slot.course_code,
                        )
                    ],
                )

            if slot.kind == SlotKind.THEORY:
                assigned_ids = self._pick_theory_faculty(
                    slot,
                    faculty_by_id,
                    loads,
                    theory_faculty_by_course_batch,
                )
            else:
                assigned_ids = self._pick_lab_faculty(
                    slot,
                    faculty_by_id,
                    loads,
                    lab_sessions,
                    problem.lab_faculty_per_session,
                )

            if not assigned_ids:
                return OptimizationSolution(
                    status=SolverStatus.INFEASIBLE,
                    objective_value=None,
                    violations=[
                        PolicyViolation(
                            code="workload_capacity_exceeded",
                            message=(
                                f"No faculty with remaining capacity for {slot.course_code} "
                                f"({slot.kind.value})."
                            ),
                            course_code=slot.course_code,
                        )
                    ],
                )

            for faculty_id in assigned_ids:
                loads[faculty_id] += slot.weekly_hours
                if slot.kind == SlotKind.LAB:
                    lab_sessions[faculty_id] += 1

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
                    lab_sub_batch=slot.lab_sub_batch,
                    faculty_ids=assigned_ids,
                    faculty_names=[faculty_by_id[fid].full_name for fid in assigned_ids],
                    requires_lecture_hall=slot.requires_lecture_hall,
                )
            )

        summaries = _build_summaries(problem, assignments)
        solution = OptimizationSolution(
            status=SolverStatus.FEASIBLE,
            objective_value=None,
            assignments=assignments,
            faculty_summaries=summaries,
            messages=["Greedy workload assignment (distinct faculty per section when possible)."],
        )
        solution.violations = validate_solution(problem, solution)
        return solution

    def _pick_theory_faculty(
        self,
        slot: AssignmentSlot,
        faculty_by_id: dict[int, object],
        loads: dict[int, int],
        theory_faculty_by_course_batch: dict[tuple[str, int], set[int]],
    ) -> list[int]:
        preferred = list(slot.specialization_matched_ids) or list(slot.eligible_faculty_ids)
        course_key = (slot.batch_code, slot.course_id)
        already_assigned = theory_faculty_by_course_batch.get(course_key, set())
        fresh = [fid for fid in preferred if fid not in already_assigned]
        faculty_id = self._lowest_load_candidate(
            fresh if fresh else preferred,
            slot.eligible_faculty_ids,
            slot.weekly_hours,
            faculty_by_id,
            loads,
        )
        if faculty_id is not None:
            theory_faculty_by_course_batch.setdefault(course_key, set()).add(faculty_id)
        return [faculty_id] if faculty_id is not None else []

    def _pick_lab_faculty(
        self,
        slot: AssignmentSlot,
        faculty_by_id: dict[int, object],
        loads: dict[int, int],
        lab_sessions: dict[int, int],
        required_count: int,
    ) -> list[int]:
        chosen: list[int] = []
        pool = list(slot.specialization_matched_ids) or list(slot.eligible_faculty_ids)
        for _ in range(required_count):
            remaining = [fid for fid in pool if fid not in chosen]
            faculty_id = self._lowest_load_candidate(
                remaining,
                slot.eligible_faculty_ids,
                slot.weekly_hours,
                faculty_by_id,
                loads,
                lab_sessions=lab_sessions,
            )
            if faculty_id is None:
                return []
            chosen.append(faculty_id)
        return chosen

    def _lowest_load_candidate(
        self,
        preferred: list[int],
        eligible: tuple[int, ...],
        hours: int,
        faculty_by_id: dict[int, object],
        loads: dict[int, int],
        lab_sessions: dict[int, int] | None = None,
    ) -> int | None:
        candidates = [fid for fid in preferred if fid in eligible]
        if not candidates:
            candidates = list(eligible)

        feasible: list[int] = []
        for faculty_id in candidates:
            feasible.append(faculty_id)

        if not feasible:
            return None
        return min(feasible, key=lambda fid: (loads[fid], fid))


def _build_summaries(
    problem: WorkloadProblem,
    assignments: list[SlotAssignment],
) -> list[FacultyWorkloadSummary]:
    summaries: list[FacultyWorkloadSummary] = []
    for faculty in problem.faculty:
        theory_hours = 0
        lab_hours = 0
        theory_courses: set[int] = set()
        lab_courses: set[int] = set()
        lab_session_count = 0

        for assignment in assignments:
            if faculty.id not in assignment.faculty_ids:
                continue
            if assignment.kind == SlotKind.THEORY.value:
                theory_hours += assignment.weekly_hours
                theory_courses.add(assignment.course_id)
            else:
                lab_hours += assignment.weekly_hours
                lab_courses.add(assignment.course_id)
                lab_session_count += 1

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
                lab_session_count=lab_session_count,
            )
        )
    return summaries
