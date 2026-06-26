"""Read services for courses, rooms, and academic structure."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.core.domain.aiml_config import DEPARTMENT_NAME
from backend.models import (
    AcademicYearLevel,
    Classroom,
    Course,
    Department,
    Laboratory,
    Semester,
)


class CourseService:
    async def list_courses(
        self,
        session: AsyncSession,
        semester_number: int | None = None,
    ) -> list[Course]:
        query = (
            select(Course)
            .join(Department)
            .where(Department.name == DEPARTMENT_NAME)
            .options(
                selectinload(Course.semester).selectinload(Semester.academic_year_level),
            )
            .order_by(Course.course_code)
        )
        if semester_number is not None:
            query = query.join(Semester).where(Semester.semester_number == semester_number)

        result = await session.execute(query)
        return list(result.scalars().unique().all())

    async def list_classrooms(self, session: AsyncSession) -> list[Classroom]:
        result = await session.execute(
            select(Classroom)
            .join(Department)
            .where(Department.name == DEPARTMENT_NAME)
            .order_by(Classroom.room_number)
        )
        return list(result.scalars().all())

    async def list_laboratories(self, session: AsyncSession) -> list[Laboratory]:
        result = await session.execute(
            select(Laboratory)
            .join(Department)
            .where(Department.name == DEPARTMENT_NAME)
            .order_by(Laboratory.room_number)
        )
        return list(result.scalars().all())

    async def list_semesters(self, session: AsyncSession) -> list[Semester]:
        result = await session.execute(
            select(Semester)
            .join(Department)
            .where(Department.name == DEPARTMENT_NAME)
            .options(selectinload(Semester.academic_year_level))
            .order_by(Semester.semester_number)
        )
        return list(result.scalars().all())

    async def list_year_levels(self, session: AsyncSession) -> list[AcademicYearLevel]:
        result = await session.execute(
            select(AcademicYearLevel)
            .join(Department)
            .where(Department.name == DEPARTMENT_NAME)
            .order_by(AcademicYearLevel.year_level)
        )
        return list(result.scalars().all())
