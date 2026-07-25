"""Schemas for faculty timetable email delivery."""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field


class FacultyTimetableMailStatus(str, Enum):
    SENT = "sent"
    SKIPPED = "skipped"
    FAILED = "failed"


class FacultyTimetableMailDetail(BaseModel):
    faculty_id: int
    full_name: str
    email: str | None = None
    status: FacultyTimetableMailStatus
    message: str


class FacultyTimetableMailResult(BaseModel):
    run_id: int
    recipient_count: int = Field(ge=0)
    sent: int = Field(ge=0)
    skipped: int = Field(ge=0)
    failed: int = Field(ge=0)
    details: list[FacultyTimetableMailDetail] = Field(default_factory=list)
