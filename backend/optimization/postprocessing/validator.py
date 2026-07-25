"""Post-solve policy checks (warnings for soft AICTE minima and maxima)."""

from __future__ import annotations

from backend.core.domain.policy_config import UNLIMITED_MAX_WEEKLY_HOURS
from backend.core.domain.teaching_load import format_teaching_load_hours
from backend.optimization.models.problem_definition import WorkloadProblem
from backend.optimization.models.solution import OptimizationSolution, PolicyViolation, SolverStatus


def validate_solution(
    problem: WorkloadProblem,
    solution: OptimizationSolution,
) -> list[PolicyViolation]:
    """Report AICTE soft-policy deviations.

    Both minimums (min theory courses / min lab sessions) and maximums (max weekly
    teaching-load hours / max lab sessions) are treated as soft: allocation is never blocked,
    but faculty outside their designation's limits are flagged as policy warnings.
    """
    if solution.status not in (SolverStatus.OPTIMAL, SolverStatus.FEASIBLE):
        return solution.violations

    violations: list[PolicyViolation] = list(solution.violations)
    summary_by_id = {summary.faculty_id: summary for summary in solution.faculty_summaries}

    for faculty in problem.faculty:
        summary = summary_by_id.get(faculty.id)
        if summary is None:
            continue
        label = faculty.designation_label or faculty.designation_key or "faculty"

        if faculty.min_theory_courses and summary.theory_course_count < faculty.min_theory_courses:
            violations.append(
                PolicyViolation(
                    code="min_theory_courses_not_met",
                    message=(
                        f"{faculty.full_name} ({label}) has {summary.theory_course_count} theory "
                        f"course(s); AICTE minimum is {faculty.min_theory_courses}."
                    ),
                    faculty_id=faculty.id,
                )
            )

        if faculty.min_lab_sessions and summary.lab_session_count < faculty.min_lab_sessions:
            violations.append(
                PolicyViolation(
                    code="min_lab_sessions_not_met",
                    message=(
                        f"{faculty.full_name} ({label}) has {summary.lab_session_count} lab "
                        f"session(s); AICTE minimum is {faculty.min_lab_sessions}."
                    ),
                    faculty_id=faculty.id,
                )
            )

        if (
            faculty.max_weekly_hours < UNLIMITED_MAX_WEEKLY_HOURS
            and summary.total_weekly_hours > faculty.max_weekly_hours
        ):
            violations.append(
                PolicyViolation(
                    code="max_weekly_hours_exceeded",
                    message=(
                        f"{faculty.full_name} ({label}) has teaching load "
                        f"{format_teaching_load_hours(summary.total_weekly_hours)} h/week "
                        f"(lab/tutorial at half weight); AICTE maximum is "
                        f"{int(faculty.max_weekly_hours)}."
                    ),
                    faculty_id=faculty.id,
                )
            )

        if (
            faculty.max_lab_sessions is not None
            and summary.lab_session_count > faculty.max_lab_sessions
        ):
            violations.append(
                PolicyViolation(
                    code="max_lab_sessions_exceeded",
                    message=(
                        f"{faculty.full_name} ({label}) is assigned {summary.lab_session_count} lab "
                        f"session(s); AICTE maximum is {faculty.max_lab_sessions}."
                    ),
                    faculty_id=faculty.id,
                )
            )

    return violations
