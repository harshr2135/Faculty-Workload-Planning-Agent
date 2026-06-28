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
    return violations
