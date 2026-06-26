"""Pydantic schemas for courses, rooms, and semesters."""

from pydantic import BaseModel, ConfigDict, Field


class CourseImportResult(BaseModel):
    created: int
    updated: int
    total_rows: int
    errors: list[str] = Field(default_factory=list)


class AcademicYearLevelRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    year_level: int
    label: str
    section_count: int
    working_days: list[str]


class SemesterRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    semester_number: int
    year_level: int
    year_label: str
    section_count: int
    working_days: list[str]


class ClassroomRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    room_number: str
    capacity: int | None = None


class LaboratoryRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    room_number: str
    capacity: int | None = None


class CourseRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    course_code: str
    name: str
    credits: int
    semester_number: int
    year_level: int
    year_label: str
    section_count: int
    lectures_per_week: int
    practical_hours: int
    has_lab: bool
