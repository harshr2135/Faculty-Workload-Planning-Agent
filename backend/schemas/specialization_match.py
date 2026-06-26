"""Schemas for course–faculty specialization matching."""

from pydantic import BaseModel, Field


class MatchedFacultyRead(BaseModel):
    faculty_id: int
    full_name: str
    designation: str
    match_reasons: list[str] = Field(default_factory=list)


class CourseSpecializationMatchRead(BaseModel):
    course_id: int
    course_code: str
    course_name: str
    inferred_keywords: list[str]
    matched_faculty: list[MatchedFacultyRead]
    fallback_required: bool
