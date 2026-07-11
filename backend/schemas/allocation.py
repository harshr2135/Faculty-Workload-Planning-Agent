"""Schemas for allocation runs."""

from pydantic import BaseModel, Field, model_validator


class PecCourseEnrollment(BaseModel):
    course_code: str = Field(examples=["23AM3605"])
    student_count: int = Field(ge=0, examples=[42])


class BatchSemesterPlan(BaseModel):
    batch_code: str = Field(examples=["2023-27"])
    semester_number: int = Field(ge=1, le=12, examples=[5])
    pec_enrollments: list[PecCourseEnrollment] = Field(
        default_factory=list,
        description="Student counts per PEC elective course. Courses with count 0 "
        "are excluded from allocation.",
    )


class AllocationRunRequest(BaseModel):
    batch_plans: list[BatchSemesterPlan] = Field(
        default_factory=list,
        description="Per-batch semester for this run. Preferred when batches differ.",
        examples=[
            [
                {"batch_code": "2022-26", "semester_number": 7},
                {"batch_code": "2023-27", "semester_number": 5},
                {"batch_code": "2024-28", "semester_number": 3},
            ]
        ],
    )
    batch_codes: list[str] = Field(
        default_factory=list,
        description="Legacy: same semester for all listed batches.",
        examples=[["2023-27"]],
    )
    batch_code: str | None = Field(
        default=None,
        description="Legacy single-batch shortcut.",
        examples=["2023-27"],
    )
    semester_number: int | None = Field(
        default=None,
        ge=1,
        le=12,
        description="Legacy: applied to every batch in batch_codes when batch_plans is empty.",
        examples=[5],
    )
    max_time_seconds: float = Field(default=120.0, ge=5.0, le=900.0)
    schedule_timetable: bool = Field(
        default=True,
        description="After workload assignment, solve weekly day/slot/room grid (Slice 2).",
    )

    @model_validator(mode="after")
    def validate_planning_input(self) -> "AllocationRunRequest":
        if self.batch_plans:
            return self
        if self.batch_code and not self.batch_codes:
            if self.semester_number is None:
                raise ValueError("semester_number is required when using batch_code.")
            return self
        if self.batch_codes and self.semester_number is None:
            raise ValueError("semester_number is required when using batch_codes without batch_plans.")
        return self


class PecCourseEnrollmentRead(BaseModel):
    course_code: str
    course_name: str = ""
    course_type: str = ""
    student_count: int = 0


class BatchSemesterPlanRead(BaseModel):
    batch_code: str
    semester_number: int
    section_count: int
    working_days: list[str]
    pec_enrollments: list[PecCourseEnrollmentRead] = Field(default_factory=list)


class PolicyViolationRead(BaseModel):
    code: str
    message: str
    faculty_id: int | None = None
    course_code: str | None = None


class SlotAssignmentRead(BaseModel):
    slot_id: str
    course_id: int
    batch_code: str = ""
    course_code: str
    course_name: str
    course_type: str
    kind: str
    section_indices: list[int]
    weekly_hours: int
    lab_sub_batch: str | None = None
    faculty_ids: list[int]
    faculty_names: list[str]


class FacultyWorkloadSummaryRead(BaseModel):
    faculty_id: int
    full_name: str
    designation_key: str | None
    theory_weekly_hours: int
    lab_weekly_hours: int
    total_weekly_hours: int
    theory_course_count: int
    lab_course_count: int
    lab_session_count: int


class TimetableEntryRead(BaseModel):
    event_id: str
    slot_id: str
    batch_code: str = ""
    course_code: str
    course_name: str
    course_type: str
    kind: str
    section_indices: list[int]
    lab_sub_batch: str | None = None
    faculty_ids: list[int]
    faculty_names: list[str]
    day: str
    period_numbers: list[int]
    period_label: str
    room_type: str
    room_name: str
    start_time: str
    end_time: str


class TimetableGridItemRead(BaseModel):
    batch_code: str
    course_code: str
    course_name: str
    course_type: str
    kind: str
    section_indices: list[int]
    lab_sub_batch: str | None = None
    faculty_names: list[str]
    room_name: str
    room_type: str
    period_label: str
    col_span: int = 1


class TimetableGridCellRead(BaseModel):
    day: str
    sort_order: int
    period_number: int | None = None
    slot_type: str = "teaching"
    fixed_label: str | None = None
    span_continuation: bool = False
    items: list[TimetableGridItemRead] = Field(default_factory=list)


class TimetableGridPeriodRead(BaseModel):
    sort_order: int
    period_number: int | None = None
    slot_type: str = "teaching"
    label: str
    start_time: str
    end_time: str
    column_header: str
    fixed_label: str | None = None


class TimetableGridRowRead(BaseModel):
    day: str
    cells: list[TimetableGridCellRead]


class TimetableGridRead(BaseModel):
    periods: list[TimetableGridPeriodRead]
    rows: list[TimetableGridRowRead]


class FacultyTimetableGridRead(BaseModel):
    faculty_id: int
    faculty_name: str
    grid: TimetableGridRead


class SectionTimetableGridRead(BaseModel):
    batch_code: str
    section_index: int
    semester_number: int
    grid: TimetableGridRead


class RoomTimetableGridRead(BaseModel):
    room_name: str
    room_type: str
    grid: TimetableGridRead


class AllocationRunSummaryRead(BaseModel):
    id: int
    plan_name: str
    is_saved: bool
    batch_codes: list[str]
    batch_label: str
    status: str
    timetable_status: str | None = None
    assignment_count: int
    created_at: str | None = None
    updated_at: str | None = None


class AllocationRunUpdateRequest(BaseModel):
    plan_name: str | None = Field(default=None, max_length=120)
    is_saved: bool | None = None
    assignments: list[SlotAssignmentRead] | None = None


class AllocationRunProgressRead(BaseModel):
    phase: str
    label: str
    percent: int = Field(ge=0, le=100)
    step: int = Field(ge=1)
    total_steps: int = Field(ge=1)


class AllocationRunRead(BaseModel):
    id: int
    plan_name: str | None = None
    is_saved: bool = False
    batch_plans: list[BatchSemesterPlanRead]
    batch_codes: list[str]
    batch_code: str
    semester_number: int | None = None
    section_count: int | None = None
    status: str
    run_state: str | None = None
    error_message: str | None = None
    progress: AllocationRunProgressRead | None = None
    started_at: str | None = None
    updated_at: str | None = None
    timetable_status: str | None = None
    objective_value: int | None
    assignment_count: int
    faculty_count: int
    timetable_entry_count: int = 0
    violations: list[PolicyViolationRead] = Field(default_factory=list)
    messages: list[str] = Field(default_factory=list)
    timetable_messages: list[str] = Field(default_factory=list)
    assignments: list[SlotAssignmentRead] = Field(default_factory=list)
    faculty_summaries: list[FacultyWorkloadSummaryRead] = Field(default_factory=list)
    timetable_entries: list[TimetableEntryRead] = Field(default_factory=list)
    timetable_grid: TimetableGridRead | None = None
    faculty_timetable_grids: list[FacultyTimetableGridRead] = Field(default_factory=list)
    section_timetable_grids: list[SectionTimetableGridRead] = Field(default_factory=list)
    classroom_timetable_grids: list[RoomTimetableGridRead] = Field(default_factory=list)
    laboratory_timetable_grids: list[RoomTimetableGridRead] = Field(default_factory=list)
