"""Excel faculty import service."""

from __future__ import annotations

from dataclasses import dataclass
from io import BytesIO
from pathlib import Path

import openpyxl
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.models import Department, FacultyMember, FacultySpecialization
from backend.schemas.faculty import FacultyImportResult

EXPECTED_HEADERS = {
    "sl. no": "serial_number",
    "name": "full_name",
    "designation": "designation",
    "department": "department",
    "email id": "email",
    "phone number": "phone",
    "domain specialization": "specializations",
    "cabin number": "cabin_number",
}


@dataclass
class FacultyRow:
    serial_number: int | None
    full_name: str
    designation: str
    department: str
    email: str
    phone: str | None
    specializations: list[str]
    cabin_number: str | None


def _normalize_header(value: object) -> str:
    return str(value or "").strip().lower()


def _parse_specializations(raw: object) -> list[str]:
    if raw is None:
        return []
    parts = [part.strip() for part in str(raw).split(",")]
    seen: set[str] = set()
    result: list[str] = []
    for part in parts:
        if not part:
            continue
        key = part.casefold()
        if key in seen:
            continue
        seen.add(key)
        result.append(part)
    return result


def _parse_serial_number(raw: object) -> int | None:
    if raw is None or str(raw).strip() == "":
        return None
    return int(raw)


def _parse_phone(raw: object) -> str | None:
    if raw is None:
        return None
    phone = str(raw).strip()
    if phone.endswith(".0"):
        phone = phone[:-2]
    return phone or None


def _build_header_map(headers: list[object]) -> dict[int, str]:
    mapping: dict[int, str] = {}
    for index, header in enumerate(headers):
        normalized = _normalize_header(header)
        field_name = EXPECTED_HEADERS.get(normalized)
        if field_name:
            mapping[index] = field_name
    return mapping


def parse_faculty_workbook(source: Path | BytesIO) -> tuple[list[FacultyRow], list[str]]:
    workbook = openpyxl.load_workbook(source, read_only=True, data_only=True)
    worksheet = workbook.active
    rows_iter = worksheet.iter_rows(values_only=True)
    errors: list[str] = []

    try:
        header_row = next(rows_iter)
    except StopIteration as exc:
        raise ValueError("Excel file is empty.") from exc

    header_map = _build_header_map(list(header_row))
    missing = sorted(set(EXPECTED_HEADERS.values()) - set(header_map.values()))
    if missing:
        raise ValueError(
            "Excel headers do not match the expected format. "
            f"Missing mapped columns: {', '.join(missing)}"
        )

    parsed_rows: list[FacultyRow] = []
    for row_number, row in enumerate(rows_iter, start=2):
        if not any(cell is not None and str(cell).strip() for cell in row):
            continue

        values: dict[str, object] = {}
        for index, field_name in header_map.items():
            values[field_name] = row[index] if index < len(row) else None

        full_name = str(values.get("full_name") or "").strip()
        email = str(values.get("email") or "").strip().lower()
        department = str(values.get("department") or "").strip()
        designation = str(values.get("designation") or "").strip()

        if not full_name:
            errors.append(f"Row {row_number}: missing name.")
            continue
        if not email:
            errors.append(f"Row {row_number}: missing email.")
            continue
        if not department:
            errors.append(f"Row {row_number}: missing department.")
            continue
        if not designation:
            errors.append(f"Row {row_number}: missing designation.")
            continue

        parsed_rows.append(
            FacultyRow(
                serial_number=_parse_serial_number(values.get("serial_number")),
                full_name=full_name,
                designation=designation,
                department=department,
                email=email,
                phone=_parse_phone(values.get("phone")),
                specializations=_parse_specializations(values.get("specializations")),
                cabin_number=str(values.get("cabin_number") or "").strip() or None,
            )
        )

    workbook.close()
    return parsed_rows, errors


async def _get_or_create_department(session: AsyncSession, name: str) -> Department:
    result = await session.execute(select(Department).where(Department.name == name))
    department = result.scalar_one_or_none()
    if department is None:
        department = Department(name=name)
        session.add(department)
        await session.flush()
    return department


class FacultyImportService:
    async def import_from_excel(
        self,
        session: AsyncSession,
        source: Path | BytesIO,
    ) -> FacultyImportResult:
        rows, parse_errors = parse_faculty_workbook(source)
        created = 0
        updated = 0
        departments: set[str] = set()

        for row in rows:
            departments.add(row.department)
            department = await _get_or_create_department(session, row.department)

            result = await session.execute(
                select(FacultyMember)
                .options(selectinload(FacultyMember.specializations))
                .where(FacultyMember.email == row.email)
            )
            faculty = result.scalar_one_or_none()

            if faculty is None:
                faculty = FacultyMember(
                    department_id=department.id,
                    serial_number=row.serial_number,
                    full_name=row.full_name,
                    designation=row.designation,
                    email=row.email,
                    phone=row.phone,
                    cabin_number=row.cabin_number,
                )
                session.add(faculty)
                await session.flush()
                created += 1
            else:
                faculty.department_id = department.id
                faculty.serial_number = row.serial_number
                faculty.full_name = row.full_name
                faculty.designation = row.designation
                faculty.phone = row.phone
                faculty.cabin_number = row.cabin_number
                for specialization in list(faculty.specializations):
                    await session.delete(specialization)
                await session.flush()
                updated += 1

            for specialization_name in row.specializations:
                session.add(
                    FacultySpecialization(
                        faculty_member_id=faculty.id,
                        name=specialization_name,
                    )
                )

        return FacultyImportResult(
            created=created,
            updated=updated,
            total_rows=len(rows),
            departments=sorted(departments),
            errors=parse_errors,
        )
