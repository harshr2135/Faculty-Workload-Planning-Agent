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


class LectureHallRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    min_combined_sections: int
    max_combined_sections: int
    capacity: int | None = None


class StudentBatchRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    batch_code: str
    default_planning_semester: int


class CourseRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    course_code: str
    name: str
    batch_code: str
    course_type: str
    credits: int
    semester_number: int
    year_level: int
    year_label: str
    section_count: int
    lectures_per_week: int
    practical_hours: int
    has_lab: bool
    requires_lecture_hall: bool
