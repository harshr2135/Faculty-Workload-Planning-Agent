"""Timetable API routes."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database.session import get_db_session
from backend.schemas.timetable import TimeSlotRead, TimetableOverviewRead
from backend.services.timetable_service import TimetableSeedService, TimetableService

router = APIRouter(prefix="/timetable", tags=["timetable"])


@router.get("/slots", response_model=list[TimeSlotRead])
async def list_time_slots(
    teaching_only: bool = Query(default=False),
    session: AsyncSession = Depends(get_db_session),
) -> list[TimeSlotRead]:
    service = TimetableService()
    slots = await service.list_time_slots(session, teaching_only=teaching_only)
    return [
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
    ]


@router.get("/overview", response_model=TimetableOverviewRead)
async def timetable_overview(
    session: AsyncSession = Depends(get_db_session),
) -> TimetableOverviewRead:
    service = TimetableService()
    return await service.get_overview(session)


@router.post("/seed-aiml")
async def seed_aiml_timetable(
    session: AsyncSession = Depends(get_db_session),
) -> dict[str, int]:
    service = TimetableSeedService()
    created = await service.seed_aiml_daily_schedule(session)
    return {"slots_created": created}
