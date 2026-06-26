"""Course–faculty specialization similarity matching."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.core.domain.aiml_config import DEPARTMENT_NAME
from backend.core.domain.policy_config import resolve_designation_key
from backend.core.domain.specialization_matcher import (
    CourseFacultyMatch,
    infer_course_keywords,
    specialization_matches_course,
)
from backend.models import Course, Department, FacultyMember


class SpecializationMatchService:
    async def get_course_matches(
        self,
        session: AsyncSession,
        semester_number: int | None = None,
    ) -> list[CourseFacultyMatch]:
        query = (
            select(Course)
            .join(Department)
            .where(Department.name == DEPARTMENT_NAME)
            .options(selectinload(Course.semester))
            .order_by(Course.course_code)
        )
        if semester_number is not None:
            from backend.models import Semester

            query = query.join(Semester).where(Semester.semester_number == semester_number)

        course_result = await session.execute(query)
        courses = list(course_result.scalars().unique().all())

        faculty_result = await session.execute(
            select(FacultyMember)
            .join(Department)
            .where(Department.name == DEPARTMENT_NAME)
            .options(selectinload(FacultyMember.specializations))
            .order_by(FacultyMember.full_name)
        )
        faculty_members = list(faculty_result.scalars().unique().all())

        matches: list[CourseFacultyMatch] = []
        for course in courses:
            keywords = infer_course_keywords(course.name)
            matched_faculty: list[dict[str, object]] = []

            for member in faculty_members:
                spec_names = [s.name for s in member.specializations]
                is_match, reasons = specialization_matches_course(spec_names, course.name)
                if is_match:
                    matched_faculty.append(
                        {
                            "faculty_id": member.id,
                            "full_name": member.full_name,
                            "designation": member.designation,
                            "match_reasons": reasons,
                        }
                    )

            matches.append(
                CourseFacultyMatch(
                    course_id=course.id,
                    course_code=course.course_code,
                    course_name=course.name,
                    inferred_keywords=keywords,
                    matched_faculty=matched_faculty,
                    fallback_required=len(matched_faculty) == 0,
                )
            )

        return matches

    async def get_fallback_faculty_ids(self, session: AsyncSession) -> list[int]:
        """Faculty IDs eligible when no specialization match (Assistant Professors)."""
        result = await session.execute(
            select(FacultyMember)
            .join(Department)
            .where(Department.name == DEPARTMENT_NAME)
        )
        return [
            member.id
            for member in result.scalars().all()
            if resolve_designation_key(member.designation) == "assistant_professor"
        ]
