"""Unit tests for Excel timetable export packs."""

from io import BytesIO

import openpyxl

from backend.schemas.allocation import (
    AllocationRunRead,
    BatchSemesterPlanRead,
    FacultyWorkloadSummaryRead,
    TimetableEntryRead,
)
from backend.services.timetable_export_service import (
    TimetableExportError,
    TimetableExportFormat,
    TimetableExportPack,
    export_filename,
    export_timetable_pack,
)
from backend.services.timetable_grid_service import (
    build_faculty_timetable_grids,
    build_room_timetable_grids,
    build_section_timetable_grids,
    build_timetable_grid,
)


def _entry(**overrides: object) -> TimetableEntryRead:
    payload = {
        "event_id": "evt-1",
        "slot_id": "slot-1",
        "batch_code": "2023-27",
        "course_code": "AIML301",
        "course_name": "Machine Learning",
        "course_type": "PCC",
        "kind": "theory",
        "section_indices": [1],
        "faculty_ids": [10],
        "faculty_names": ["Dr A"],
        "day": "monday",
        "period_numbers": [1],
        "period_label": "P1",
        "room_type": "classroom",
        "room_name": "424",
        "start_time": "08:30",
        "end_time": "09:25",
    }
    payload.update(overrides)
    return TimetableEntryRead(**payload)


def _run_with_grids() -> AllocationRunRead:
    entries = [
        _entry(),
        _entry(
            event_id="evt-2",
            slot_id="slot-2",
            kind="lab",
            lab_sub_batch="B1",
            period_numbers=[3, 4],
            period_label="P3-P4",
            room_type="laboratory",
            room_name="Lab-1",
            faculty_ids=[10, 20],
            faculty_names=["Dr A", "Dr B"],
            start_time="10:45",
            end_time="12:35",
        ),
    ]
    summaries = [
        FacultyWorkloadSummaryRead(
            faculty_id=10,
            full_name="Dr A",
            designation_key="assistant_professor",
            theory_weekly_hours=1,
            lab_weekly_hours=2,
            total_weekly_hours=2,
            theory_course_count=1,
            lab_course_count=1,
            lab_session_count=1,
        ),
        FacultyWorkloadSummaryRead(
            faculty_id=20,
            full_name="Dr B",
            designation_key="assistant_professor",
            theory_weekly_hours=0,
            lab_weekly_hours=2,
            total_weekly_hours=1,
            theory_course_count=0,
            lab_course_count=1,
            lab_session_count=1,
        ),
    ]
    plans = [
        BatchSemesterPlanRead(
            batch_code="2023-27",
            semester_number=5,
            section_count=1,
            working_days=["monday", "tuesday", "wednesday", "thursday", "friday"],
        )
    ]
    return AllocationRunRead(
        id=42,
        batch_plans=plans,
        batch_codes=["2023-27"],
        batch_code="2023-27",
        semester_number=5,
        section_count=1,
        status="feasible",
        timetable_status="feasible",
        objective_value=None,
        assignment_count=2,
        faculty_count=2,
        timetable_entry_count=2,
        faculty_summaries=summaries,
        timetable_entries=entries,
        timetable_grid=build_timetable_grid(entries),
        faculty_timetable_grids=build_faculty_timetable_grids(entries, summaries),
        section_timetable_grids=build_section_timetable_grids(entries, plans),
        classroom_timetable_grids=build_room_timetable_grids(entries, "classroom"),
        laboratory_timetable_grids=build_room_timetable_grids(entries, "laboratory"),
    )


def test_export_faculty_pack_has_one_sheet_per_faculty() -> None:
    run = _run_with_grids()
    payload = export_timetable_pack(run, TimetableExportPack.FACULTY)
    workbook = openpyxl.load_workbook(BytesIO(payload))
    assert "Dr_A" in workbook.sheetnames
    assert "Dr_B" in workbook.sheetnames
    assert export_filename(run, TimetableExportPack.FACULTY) == "AIML_Faculty_Timetable_run42.xlsx"


def test_export_students_pack_has_section_sheet() -> None:
    run = _run_with_grids()
    payload = export_timetable_pack(run, TimetableExportPack.STUDENTS)
    workbook = openpyxl.load_workbook(BytesIO(payload))
    assert "2023-27_Sec1" in workbook.sheetnames
    sheet = workbook["2023-27_Sec1"]
    assert "Class timetable" in str(sheet["A1"].value)


def test_export_rooms_pack_includes_classrooms_and_labs() -> None:
    run = _run_with_grids()
    payload = export_timetable_pack(run, TimetableExportPack.ROOMS)
    workbook = openpyxl.load_workbook(BytesIO(payload))
    assert "CR_424" in workbook.sheetnames
    assert "Lab_Lab-1" in workbook.sheetnames


def test_export_pdf_faculty_pack_is_valid_pdf() -> None:
    run = _run_with_grids()
    payload = export_timetable_pack(run, TimetableExportPack.FACULTY, TimetableExportFormat.PDF)
    assert payload.startswith(b"%PDF")
    assert (
        export_filename(run, TimetableExportPack.FACULTY, TimetableExportFormat.PDF)
        == "AIML_Faculty_Timetable_run42.pdf"
    )


def test_export_pdf_students_and_rooms_packs() -> None:
    run = _run_with_grids()
    students = export_timetable_pack(run, TimetableExportPack.STUDENTS, TimetableExportFormat.PDF)
    rooms = export_timetable_pack(run, TimetableExportPack.ROOMS, TimetableExportFormat.PDF)
    assert students.startswith(b"%PDF")
    assert rooms.startswith(b"%PDF")


def test_export_empty_pack_raises() -> None:
    run = AllocationRunRead(
        id=1,
        batch_plans=[],
        batch_codes=[],
        batch_code="2023-27",
        semester_number=5,
        status="feasible",
        objective_value=None,
        assignment_count=0,
        faculty_count=0,
        timetable_entry_count=0,
        faculty_timetable_grids=[],
        section_timetable_grids=[],
        classroom_timetable_grids=[],
        laboratory_timetable_grids=[],
    )
    try:
        export_timetable_pack(run, TimetableExportPack.FACULTY)
        raised = False
    except TimetableExportError:
        raised = True
    assert raised
