"""Shared CP-SAT solver performance settings."""

from __future__ import annotations

import os

from ortools.sat.python import cp_model


def apply_cpsat_performance(
    solver: cp_model.CpSolver,
    max_time_seconds: float,
    *,
    stop_after_first_solution: bool = False,
    num_search_workers: int | None = None,
) -> None:
    """Apply wall-clock and parallel search settings to a CP-SAT solver."""
    solver.parameters.max_time_in_seconds = max_time_seconds
    workers = num_search_workers
    if workers is None:
        workers = min(8, os.cpu_count() or 4)
    solver.parameters.num_search_workers = workers
    if stop_after_first_solution:
        solver.parameters.stop_after_first_solution = True
