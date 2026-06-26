"""Timetable grid output contracts."""

from __future__ import annotations

from dataclasses import dataclass, field

from backend.optimization.models.solution import SolverStatus


@dataclass(frozen=True)
class TimetableEntry:
    event_id: str
    slot_id: str
    batch_code: str
    course_code: str
    course_name: str
    course_type: str
    kind: str
    section_indices: list[int]
    faculty_ids: list[int]
    faculty_names: list[str]
    day: str
    period_numbers: list[int]
    period_label: str
    room_type: str
    room_name: str
    start_time: str
    end_time: str


@dataclass
class TimetableSolution:
    status: SolverStatus
    entries: list[TimetableEntry] = field(default_factory=list)
    messages: list[str] = field(default_factory=list)
