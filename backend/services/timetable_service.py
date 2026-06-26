"""Timetable slot read and seed services."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.domain.aiml_config import DEPARTMENT_NAME
from backend.core.domain.timetable_config import AIML_DAILY_SCHEDULE, TEACHING_PERIODS_PER_DAY
from backend.models import Department, TimeSlot
from backend.schemas.timetable import TimetableOverviewRead, TimeSlotRead


class TimetableService:
    async def list_time_slots(
        self,
        session: AsyncSession,
        teaching_only: bool = False,
    ) -> list[TimeSlot]:
        query = (
            select(TimeSlot)
            .join(Department)
            .where(Department.name == DEPARTMENT_NAME)
            .order_by(TimeSlot.sort_order)
        )
        if teaching_only:
            query = query.where(TimeSlot.slot_type == "teaching")

        result = await session.execute(query)
        return list(result.scalars().all())

    async def get_overview(self, session: AsyncSession) -> TimetableOverviewRead:
        slots = await self.list_time_slots(session)
        return TimetableOverviewRead(
            teaching_periods_per_day=TEACHING_PERIODS_PER_DAY,
            total_periods_in_day=len(slots),
            slots=[
                TimeSlotRead(
                    id=slot.id,
                    sort_order=slot.sort_order,
                    period_number=slot.period_number,
                    label=slot.label,
                    start_time=slot.start_time,
                    end_time=slot.end_time,
                    slot_type=slot.slot_type,
                    duration_minutes=slot.duration_minutes,
                    is_teaching_slot=slot.is_teaching_slot,
                )
                for slot in slots
            ],
        )


class TimetableSeedService:
    async def seed_aiml_daily_schedule(self, session: AsyncSession) -> int:
        result = await session.execute(
            select(Department).where(Department.name == DEPARTMENT_NAME)
        )
        department = result.scalar_one_or_none()
        if department is None:
            raise ValueError(
                f"Department '{DEPARTMENT_NAME}' not found. Run seed_aiml_master_data first."
            )

        created = 0
        for period in AIML_DAILY_SCHEDULE:
            existing = await session.scalar(
                select(TimeSlot.id).where(
                    TimeSlot.department_id == department.id,
                    TimeSlot.sort_order == period.sort_order,
                )
            )
            if existing is None:
                session.add(
                    TimeSlot(
                        department_id=department.id,
                        sort_order=period.sort_order,
                        period_number=period.period_number,
                        label=period.label,
                        start_time=period.start_time,
                        end_time=period.end_time,
                        slot_type=period.slot_type,
                    )
                )
                created += 1
            else:
                slot = await session.get(TimeSlot, existing)
                if slot is not None:
                    slot.period_number = period.period_number
                    slot.label = period.label
                    slot.start_time = period.start_time
                    slot.end_time = period.end_time
                    slot.slot_type = period.slot_type

        await session.flush()
        return created
