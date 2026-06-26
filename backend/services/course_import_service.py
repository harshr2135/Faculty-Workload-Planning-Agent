"""Course Excel import service."""

from __future__ import annotations

from dataclasses import dataclass
from io import BytesIO
from pathlib import Path

import openpyxl
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.domain.aiml_config import DEPARTMENT_NAME, SEMESTER_TO_YEAR_LEVEL
from backend.models import Course, Department, Semester
from backend.schemas.course import CourseImportResult

EXPECTED_HEADERS = {
    "semester": "semester_number",
    "subject": "name",
    "course code": "course_code",
    "credits": "credits",
    "number of lectures per week": "lectures_per_week",
    "practical": "practical_hours",
}


@dataclass
class CourseRow:
    semester_number: int
    name: str
    course_code: str
    credits: int
    lectures_per_week: int
    practical_hours: int


def _normalize_header(value: object) -> str:
    return str(value or "").strip().lower()


def _build_header_map(headers: list[object]) -> dict[int, str]:
    mapping: dict[int, str] = {}
    for index, header in enumerate(headers):
        normalized = _normalize_header(header)
        field_name = EXPECTED_HEADERS.get(normalized)
        if field_name:
            mapping[index] = field_name
    return mapping


def _to_int(value: object, field: str, row_number: int) -> int:
    if value is None or str(value).strip() == "":
        raise ValueError(f"Row {row_number}: missing {field}.")
    if isinstance(value, float):
        return int(value)
    return int(value)


def parse_courses_workbook(source: Path | BytesIO) -> tuple[list[CourseRow], list[str]]:
    workbook = openpyxl.load_workbook(source, read_only=True, data_only=True)
    worksheet = workbook.active
    rows_iter = worksheet.iter_rows(values_only=True)
    errors: list[str] = []

    header_row = None
    for row in rows_iter:
        if row and any(
            _normalize_header(cell) in EXPECTED_HEADERS for cell in row if cell is not None
        ):
            header_row = row
            break

    if header_row is None:
        workbook.close()
        raise ValueError("Could not find course header row in Excel file.")

    header_map = _build_header_map(list(header_row))
    missing = sorted(set(EXPECTED_HEADERS.values()) - set(header_map.values()))
    if missing:
        workbook.close()
        raise ValueError(f"Missing required columns: {', '.join(missing)}")

    parsed_rows: list[CourseRow] = []
    row_number = 0
    for row in rows_iter:
        row_number += 1
        if not any(cell is not None and str(cell).strip() for cell in row):
            continue

        values: dict[str, object] = {}
        for index, field_name in header_map.items():
            values[field_name] = row[index] if index < len(row) else None

        semester_raw = values.get("semester_number")
        if semester_raw is None:
            continue

        try:
            semester_number = _to_int(semester_raw, "semester", row_number)
            credits = _to_int(values.get("credits"), "credits", row_number)
            lectures_per_week = _to_int(
                values.get("lectures_per_week"), "lectures per week", row_number
            )
            practical_hours = _to_int(
                values.get("practical_hours"), "practical hours", row_number
            )
        except ValueError as exc:
            errors.append(str(exc))
            continue

        name = str(values.get("name") or "").strip()
        course_code = str(values.get("course_code") or "").strip().upper()
        if not name:
            errors.append(f"Row {row_number}: missing subject name.")
            continue
        if not course_code:
            errors.append(f"Row {row_number}: missing course code.")
            continue
        if semester_number not in SEMESTER_TO_YEAR_LEVEL:
            errors.append(f"Row {row_number}: unsupported semester {semester_number}.")
            continue

        parsed_rows.append(
            CourseRow(
                semester_number=semester_number,
                name=name,
                course_code=course_code,
                credits=credits,
                lectures_per_week=lectures_per_week,
                practical_hours=practical_hours,
            )
        )

    workbook.close()
    return parsed_rows, errors


class CourseImportService:
    async def import_from_excel(
        self,
        session: AsyncSession,
        source: Path | BytesIO,
        department_name: str = DEPARTMENT_NAME,
    ) -> CourseImportResult:
        rows, parse_errors = parse_courses_workbook(source)
        created = 0
        updated = 0

        dept_result = await session.execute(
            select(Department).where(Department.name == department_name)
        )
        department = dept_result.scalar_one_or_none()
        if department is None:
            raise ValueError(
                f"Department '{department_name}' not found. Run seed_aiml_master_data first."
            )

        for row in rows:
            sem_result = await session.execute(
                select(Semester).where(
                    Semester.department_id == department.id,
                    Semester.semester_number == row.semester_number,
                )
            )
            semester = sem_result.scalar_one_or_none()
            if semester is None:
                parse_errors.append(
                    f"Semester {row.semester_number} not configured for {department_name}."
                )
                continue

            course_result = await session.execute(
                select(Course).where(
                    Course.department_id == department.id,
                    Course.course_code == row.course_code,
                )
            )
            course = course_result.scalar_one_or_none()

            if course is None:
                course = Course(
                    department_id=department.id,
                    semester_id=semester.id,
                    name=row.name,
                    course_code=row.course_code,
                    credits=row.credits,
                    lectures_per_week=row.lectures_per_week,
                    practical_hours=row.practical_hours,
                )
                session.add(course)
                created += 1
            else:
                course.semester_id = semester.id
                course.name = row.name
                course.credits = row.credits
                course.lectures_per_week = row.lectures_per_week
                course.practical_hours = row.practical_hours
                updated += 1

        await session.flush()
        return CourseImportResult(
            created=created,
            updated=updated,
            total_rows=len(rows),
            errors=parse_errors,
        )
