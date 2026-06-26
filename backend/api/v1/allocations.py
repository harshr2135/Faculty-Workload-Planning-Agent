"""Allocation run API routes."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database.session import get_db_session
from backend.schemas.allocation import (
    AllocationRunRead,
    AllocationRunRequest,
    BatchSemesterPlan,
)
from backend.services.allocation_service import AllocationService

router = APIRouter(tags=["allocations"])


def _resolve_request_plans(body: AllocationRunRequest) -> list[BatchSemesterPlan]:
    if body.batch_plans:
        return body.batch_plans

    batch_codes = list(body.batch_codes)
    if not batch_codes and body.batch_code:
        batch_codes = [body.batch_code]

    if batch_codes:
        if body.semester_number is None:
            raise ValueError("semester_number is required when batch_plans is not provided.")
        return [
            BatchSemesterPlan(batch_code=code, semester_number=body.semester_number)
            for code in batch_codes
        ]

    return []


@router.post("/allocations/run", response_model=AllocationRunRead)
async def run_allocation(
    body: AllocationRunRequest,
    session: AsyncSession = Depends(get_db_session),
) -> AllocationRunRead:
    """Run CP-SAT workload + weekly timetable for one or more batches (each with its semester)."""
    service = AllocationService()
    try:
        batch_plans = _resolve_request_plans(body)
        return await service.run_allocation(
            session,
            batch_plans=batch_plans or None,
            max_time_seconds=body.max_time_seconds,
            schedule_timetable=body.schedule_timetable,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.get("/allocations/{run_id}", response_model=AllocationRunRead)
async def get_allocation_run(
    run_id: int,
    session: AsyncSession = Depends(get_db_session),
) -> AllocationRunRead:
    service = AllocationService()
    result = await service.get_run(session, run_id)
    if result is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Allocation run not found.")
    return result
