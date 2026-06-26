"""Post-solve policy checks (warnings for soft / departmental minima)."""

from __future__ import annotations

from backend.optimization.models.problem_definition import WorkloadProblem
from backend.optimization.models.solution import OptimizationSolution, PolicyViolation, SolverStatus


def validate_solution(
    problem: WorkloadProblem,
    solution: OptimizationSolution,
) -> list[PolicyViolation]:
    if solution.status not in (SolverStatus.OPTIMAL, SolverStatus.FEASIBLE):
        return solution.violations

    violations: list[PolicyViolation] = []
    faculty_by_id = {member.id: member for member in problem.faculty}

    for summary in solution.faculty_summaries:
        policy = faculty_by_id.get(summary.faculty_id)
        if policy is None:
            continue

        if summary.total_weekly_hours > int(policy.max_weekly_hours):
            violations.append(
                PolicyViolation(
                    code="max_weekly_hours_exceeded",
                    message=(
                        f"{summary.full_name} exceeds max weekly hours "
                        f"({summary.total_weekly_hours} > {policy.max_weekly_hours})."
                    ),
                    faculty_id=summary.faculty_id,
                )
            )

        if (
            policy.max_lab_sessions is not None
            and summary.lab_session_count > policy.max_lab_sessions
        ):
            violations.append(
                PolicyViolation(
                    code="max_lab_sessions_exceeded",
                    message=(
                        f"{summary.full_name} has {summary.lab_session_count} lab sessions; "
                        f"maximum is {policy.max_lab_sessions}."
                    ),
                    faculty_id=summary.faculty_id,
                )
            )

    return violations
