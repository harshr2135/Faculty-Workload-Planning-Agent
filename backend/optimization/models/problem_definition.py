"""Input contracts for the workload allocation optimizer (Slice 1)."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from backend.core.domain.course_type_config import supports_lab_practicals


class SlotKind(str, Enum):
    THEORY = "theory"
    LAB = "lab"


@dataclass(frozen=True)
class FacultyInput:
    id: int
    full_name: str
    designation_key: str | None
    designation_label: str
    min_weekly_hours: float
    max_weekly_hours: float
    min_theory_courses: int
    min_lab_courses: int
    min_lab_sessions: int | None
    max_lab_sessions: int | None


@dataclass(frozen=True)
class CourseInput:
    id: int
    batch_code: str
    semester_number: int
    section_count: int
    working_days: tuple[str, ...]
    course_code: str
    name: str
    course_type: str
    lectures_per_week: int
    practical_hours: int
    requires_lecture_hall: bool

    @property
    def has_lab(self) -> bool:
        return supports_lab_practicals(self.course_type, self.practical_hours)


@dataclass(frozen=True)
class AssignmentSlot:
    """Atomic unit the solver must staff (theory or lab)."""

    slot_id: str
    course_id: int
    batch_code: str
    working_days: tuple[str, ...]
    course_code: str
    course_name: str
    course_type: str
    kind: SlotKind
    section_indices: tuple[int, ...]
    weekly_hours: int
    eligible_faculty_ids: tuple[int, ...]
    specialization_matched_ids: tuple[int, ...]
    fallback_required: bool
    requires_lecture_hall: bool = False
    lab_sub_batch: str | None = None


@dataclass(frozen=True)
class BatchPlanInput:
    batch_code: str
    semester_number: int
    section_count: int
    working_days: tuple[str, ...]


@dataclass(frozen=True)
class WorkloadProblem:
    batch_plans: tuple[BatchPlanInput, ...]
    lab_faculty_per_session: int
    faculty: tuple[FacultyInput, ...]
    courses: tuple[CourseInput, ...]
    slots: tuple[AssignmentSlot, ...]
    lecture_hall_min_sections: int = 2
    lecture_hall_max_sections: int = 3


@dataclass
class SolverConfig:
    max_time_seconds: float = 60.0
    hours_scale: int = 1
    mismatch_penalty: int = 50
    fallback_penalty: int = 200
    balance_penalty: int = 10
    stop_after_first_solution: bool = False
