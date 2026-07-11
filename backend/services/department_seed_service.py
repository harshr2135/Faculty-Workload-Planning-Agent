"""Seed AIML department classrooms, labs, semesters, and year-level rules."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.core.domain.aiml_config import (
    AIML_YEAR_LEVELS,
    CLASSROOM_NUMBERS,
    DEPARTMENT_NAME,
    LABORATORY_NUMBERS,
    LECTURE_HALL_MAX_COMBINED_SECTIONS,
    LECTURE_HALL_MIN_COMBINED_SECTIONS,
    LECTURE_HALL_NAMES,
    STUDENT_BATCH_CODES,
)
from backend.core.domain.lab_config import LAB_MAX_CAPACITY
from backend.models import AcademicYearLevel, Classroom, Department, Laboratory, LectureHall, Semester, StudentBatch


async def _get_or_create_department(session: AsyncSession, name: str) -> Department:
    result = await session.execute(select(Department).where(Department.name == name))
    department = result.scalar_one_or_none()
    if department is None:
        department = Department(name=name)
        session.add(department)
        await session.flush()
    return department


class DepartmentSeedService:
    async def seed_aiml_resources(self, session: AsyncSession) -> dict[str, int]:
        department = await _get_or_create_department(session, DEPARTMENT_NAME)

        classrooms_created = await self._seed_classrooms(session, department.id)
        laboratories_created = await self._seed_laboratories(session, department.id)
        lecture_halls_created = await self._seed_lecture_halls(session)
        batches_created = await self._seed_student_batches(session, department.id)
        year_levels_created, semesters_created = await self._seed_academic_structure(
            session, department.id
        )
        from backend.services.timetable_service import TimetableSeedService  # noqa: PLC0415

        timetable_created = await TimetableSeedService().seed_aiml_daily_schedule(session)
        from backend.services.policy_service import PolicySeedService  # noqa: PLC0415

        policy_result = await PolicySeedService().seed_aiml_policies(session)

        await session.flush()
        return {
            "classrooms_created": classrooms_created,
            "laboratories_created": laboratories_created,
            "lecture_halls_created": lecture_halls_created,
            "student_batches_created": batches_created,
            "year_levels_created": year_levels_created,
            "semesters_created": semesters_created,
            "timetable_slots_created": timetable_created,
            "designation_policies_created": policy_result["designation_policies_created"],
            "planning_policies_created": policy_result["planning_policies_created"],
        }

    async def _seed_classrooms(self, session: AsyncSession, department_id: int) -> int:
        created = 0
        for room_number in CLASSROOM_NUMBERS:
            exists = await session.scalar(
                select(Classroom.id).where(
                    Classroom.department_id == department_id,
                    Classroom.room_number == room_number,
                )
            )
            if exists is None:
                session.add(Classroom(department_id=department_id, room_number=room_number))
                created += 1
        await session.flush()
        return created

    async def _seed_laboratories(self, session: AsyncSession, department_id: int) -> int:
        created = 0
        for room_number in LABORATORY_NUMBERS:
            exists = await session.scalar(
                select(Laboratory.id).where(
                    Laboratory.department_id == department_id,
                    Laboratory.room_number == room_number,
                )
            )
            if exists is None:
                session.add(
                    Laboratory(
                        department_id=department_id,
                        room_number=room_number,
                        capacity=LAB_MAX_CAPACITY,
                    )
                )
                created += 1
            else:
                row = await session.get(Laboratory, exists)
                if row is not None and row.capacity is None:
                    row.capacity = LAB_MAX_CAPACITY
        await session.flush()
        return created

    async def _seed_lecture_halls(self, session: AsyncSession) -> int:
        created = 0
        legacy_halls = await session.execute(
            select(LectureHall).where(LectureHall.name.like("LH-%"))
        )
        for row in legacy_halls.scalars():
            suffix = row.name.removeprefix("LH-")
            if suffix.isdigit():
                row.name = f"LH{suffix}"
        await session.flush()

        for name in LECTURE_HALL_NAMES:
            exists = await session.scalar(select(LectureHall.id).where(LectureHall.name == name))
            if exists is None:
                session.add(
                    LectureHall(
                        name=name,
                        min_combined_sections=LECTURE_HALL_MIN_COMBINED_SECTIONS,
                        max_combined_sections=LECTURE_HALL_MAX_COMBINED_SECTIONS,
                    )
                )
                created += 1
            else:
                row = await session.get(LectureHall, exists)
                if row is not None:
                    row.min_combined_sections = LECTURE_HALL_MIN_COMBINED_SECTIONS
                    row.max_combined_sections = LECTURE_HALL_MAX_COMBINED_SECTIONS
        await session.flush()
        return created

    async def _seed_student_batches(self, session: AsyncSession, department_id: int) -> int:
        created = 0
        for batch_code in STUDENT_BATCH_CODES:
            exists = await session.scalar(
                select(StudentBatch.id).where(
                    StudentBatch.department_id == department_id,
                    StudentBatch.batch_code == batch_code,
                )
            )
            if exists is None:
                session.add(StudentBatch(department_id=department_id, batch_code=batch_code))
                created += 1
        await session.flush()
        return created

    async def _seed_academic_structure(
        self,
        session: AsyncSession,
        department_id: int,
    ) -> tuple[int, int]:
        year_levels_created = 0
        semesters_created = 0

        for config in AIML_YEAR_LEVELS:
            result = await session.execute(
                select(AcademicYearLevel).where(
                    AcademicYearLevel.department_id == department_id,
                    AcademicYearLevel.year_level == config.year_level,
                )
            )
            year_level = result.scalar_one_or_none()
            if year_level is None:
                year_level = AcademicYearLevel(
                    department_id=department_id,
                    year_level=config.year_level,
                    label=config.label,
                    section_count=config.section_count,
                    working_days=config.working_days,
                )
                session.add(year_level)
                await session.flush()
                year_levels_created += 1
            else:
                year_level.label = config.label
                year_level.section_count = config.section_count
                year_level.working_days = config.working_days

            for semester_number in config.semester_numbers:
                sem_result = await session.execute(
                    select(Semester).where(
                        Semester.department_id == department_id,
                        Semester.semester_number == semester_number,
                    )
                )
                semester = sem_result.scalar_one_or_none()
                if semester is None:
                    session.add(
                        Semester(
                            department_id=department_id,
                            academic_year_level_id=year_level.id,
                            semester_number=semester_number,
                        )
                    )
                    semesters_created += 1
                else:
                    semester.academic_year_level_id = year_level.id

        await session.flush()
        return year_levels_created, semesters_created

    async def get_department_overview(self, session: AsyncSession) -> Department | None:
        result = await session.execute(
            select(Department)
            .where(Department.name == DEPARTMENT_NAME)
            .options(
                selectinload(Department.classrooms),
                selectinload(Department.laboratories),
                selectinload(Department.academic_year_levels),
                selectinload(Department.semesters).selectinload(Semester.academic_year_level),
            )
        )
        return result.scalar_one_or_none()
