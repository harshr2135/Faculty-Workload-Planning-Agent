"""Faculty management service."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.models import FacultyMember


class FacultyService:
    async def list_faculty(self, session: AsyncSession) -> list[FacultyMember]:
        result = await session.execute(
            select(FacultyMember)
            .options(
                selectinload(FacultyMember.specializations),
                selectinload(FacultyMember.department),
            )
            .order_by(FacultyMember.serial_number.nulls_last(), FacultyMember.full_name)
        )
        return list(result.scalars().all())
