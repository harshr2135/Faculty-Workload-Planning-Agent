"""Course Excel import service."""

from __future__ import annotations

from dataclasses import dataclass
from io import BytesIO
from pathlib import Path

import openpyxl
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.domain.aiml_config import DEPARTMENT_NAME, SEMESTER_TO_YEAR_LEVEL
from backend.core.domain.course_type_config import validate_course_type
from backend.models import Course, Department, Semester, StudentBatch
from backend.schemas.course import CourseImportResult

EXPECTED_HEADERS = {
    "semester": "semester_number",
    "course type": "course_type",
    "subject": "name",
    "course code": "course_code",
    "credits": "credits",
    "number of lectures per week": "lectures_per_week",
    "practical": "practical_hours",
}


@dataclass
class CourseRow:
    batch_code: str
    semester_number: int
    course_type: str
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


def _normalize_batch_code(value: object) -> str:
    text = str(value or "").strip()
    if not text:
        return ""
    if isinstance(value, float):
        text = str(int(value))
    return text


def parse_courses_workbook(source: Path | BytesIO) -> tuple[list[CourseRow], list[str]]:
    workbook = openpyxl.load_workbook(source, read_only=True, data_only=True)
    worksheet = workbook.active
    rows_iter = worksheet.iter_rows(values_only=True)
    errors: list[str] = []

    header_row = None
    header_row_index = 0
    for row in rows_iter:
        header_row_index += 1
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

    semester_columns = [
        index for index, field in header_map.items() if field == "semester_number"
    ]
    batch_column_index = semester_columns[0] - 1 if semester_columns and semester_columns[0] > 0 else 0

    parsed_rows: list[CourseRow] = []
    row_number = header_row_index
    current_batch = ""
    for row in rows_iter:
        row_number += 1
        if not any(cell is not None and str(cell).strip() for cell in row):
            continue

        values: dict[str, object] = {}
        for index, field_name in header_map.items():
            values[field_name] = row[index] if index < len(row) else None

        batch_raw = row[batch_column_index] if batch_column_index < len(row) else None
        batch_code = _normalize_batch_code(batch_raw)
        if batch_code:
            current_batch = batch_code
        elif current_batch:
            batch_code = current_batch
        else:
            errors.append(f"Row {row_number}: missing student batch.")
            continue

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
            course_type = validate_course_type(str(values.get("course_type") or ""))
        except ValueError as exc:
            errors.append(str(exc) if str(exc).startswith("Row") else f"Row {row_number}: {exc}")
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
                batch_code=batch_code,
                semester_number=semester_number,
                course_type=course_type,
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
    async def _get_or_create_batch(
        self,
        session: AsyncSession,
        department_id: int,
        batch_code: str,
    ) -> StudentBatch:
        result = await session.execute(
            select(StudentBatch).where(
                StudentBatch.department_id == department_id,
                StudentBatch.batch_code == batch_code,
            )
        )
        batch = result.scalar_one_or_none()
        if batch is None:
            batch = StudentBatch(department_id=department_id, batch_code=batch_code)
            session.add(batch)
            await session.flush()
        return batch

    async def import_from_excel(
        self,
        session: AsyncSession,
        source: Path | BytesIO,
        department_name: str = DEPARTMENT_NAME,
        replace_catalog: bool = False,
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

        if replace_catalog:
            await session.execute(delete(Course).where(Course.department_id == department.id))

        batch_cache: dict[str, StudentBatch] = {}
        for row in rows:
            if row.batch_code not in batch_cache:
                batch_cache[row.batch_code] = await self._get_or_create_batch(
                    session,
                    department.id,
                    row.batch_code,
                )
            batch = batch_cache[row.batch_code]

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
                    Course.batch_id == batch.id,
                    Course.semester_id == semester.id,
                    Course.course_code == row.course_code,
                )
            )
            course = course_result.scalar_one_or_none()

            if course is None:
                course = Course(
                    department_id=department.id,
                    batch_id=batch.id,
                    semester_id=semester.id,
                    course_type=row.course_type,
                    name=row.name,
                    course_code=row.course_code,
                    credits=row.credits,
                    lectures_per_week=row.lectures_per_week,
                    practical_hours=row.practical_hours,
                )
                session.add(course)
                created += 1
            else:
                course.batch_id = batch.id
                course.semester_id = semester.id
                course.course_type = row.course_type
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
