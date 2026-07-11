"""Timetable scheduling input contracts (Slice 2)."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class RoomKind(str, Enum):
    CLASSROOM = "classroom"
    LECTURE_HALL = "lecture_hall"
    LABORATORY = "laboratory"
    NONE = "none"


@dataclass(frozen=True)
class RoomInput:
    id: int
    name: str
    kind: RoomKind


@dataclass(frozen=True)
class PeriodInfo:
    period_number: int
    label: str
    start_time: str
    end_time: str


@dataclass(frozen=True)
class ScheduleEvent:
    """One schedulable block on the weekly grid."""

    event_id: str
    slot_id: str
    batch_code: str
    working_days: tuple[str, ...]
    course_id: int
    course_code: str
    course_name: str
    course_type: str
    kind: str
    section_indices: tuple[int, ...]
    faculty_ids: tuple[int, ...]
    faculty_names: tuple[str, ...]
    duration_periods: int
    room_kind: RoomKind
    session_index: int = 0
    lab_sub_batch: str | None = None


@dataclass(frozen=True)
class TimetableProblem:
    batch_codes: tuple[str, ...]
    working_days: tuple[str, ...]
    teaching_periods: tuple[int, ...]
    period_info: tuple[PeriodInfo, ...]
    classrooms: tuple[RoomInput, ...]
    lecture_halls: tuple[RoomInput, ...]
    laboratories: tuple[RoomInput, ...]
    events: tuple[ScheduleEvent, ...]
    consecutive_blocks: dict[int, tuple[tuple[int, ...], ...]]
    fixed_placements: tuple[FixedTimetablePlacement, ...] = ()


@dataclass(frozen=True)
class FixedTimetablePlacement:
    """Pre-placed slot used to block time (phase 1) and room (phase 2) in incremental runs."""

    day: str
    period_block: tuple[int, ...]
    room_id: int
    faculty_ids: tuple[int, ...]
    batch_code: str
    section_indices: tuple[int, ...]


@dataclass(frozen=True)
class TimetableSolverConfig:
    max_time_seconds: float = 90.0
    stop_after_first_solution: bool = True
    num_search_workers: int | None = None
