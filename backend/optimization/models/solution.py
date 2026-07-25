"""Output contracts for the workload allocation optimizer."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class SolverStatus(str, Enum):
    OPTIMAL = "optimal"
    FEASIBLE = "feasible"
    INFEASIBLE = "infeasible"
    UNKNOWN = "unknown"
    TIMEOUT = "timeout"


@dataclass(frozen=True)
class SlotAssignment:
    slot_id: str
    course_id: int
    batch_code: str
    working_days: tuple[str, ...]
    course_code: str
    course_name: str
    course_type: str
    kind: str
    section_indices: list[int]
    weekly_hours: int
    faculty_ids: list[int]
    faculty_names: list[str]
    requires_lecture_hall: bool = False
    lab_sub_batch: str | None = None


@dataclass(frozen=True)
class FacultyWorkloadSummary:
    faculty_id: int
    full_name: str
    designation_key: str | None
    theory_weekly_hours: int
    lab_weekly_hours: int
    # Teaching load toward AICTE caps (theory + lab/2 + tutorial/2), not raw contact total.
    total_weekly_hours: float
    theory_course_count: int
    lab_course_count: int
    lab_session_count: int


@dataclass(frozen=True)
class PolicyViolation:
    code: str
    message: str
    faculty_id: int | None = None
    course_code: str | None = None


@dataclass
class OptimizationSolution:
    status: SolverStatus
    objective_value: int | None
    assignments: list[SlotAssignment] = field(default_factory=list)
    faculty_summaries: list[FacultyWorkloadSummary] = field(default_factory=list)
    violations: list[PolicyViolation] = field(default_factory=list)
    messages: list[str] = field(default_factory=list)
