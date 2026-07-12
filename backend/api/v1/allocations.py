"""Allocation run API routes."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database.session import get_db_session
from backend.schemas.allocation import (
    AllocationRunRead,
    AllocationRunRequest,
    AllocationRunSummaryRead,
    AllocationRunUpdateRequest,
    BatchSemesterPlan,
)
from backend.schemas.allocation_report import BatchReportRequest, BatchReportResponse
from backend.ai.services.report_service import build_batch_report
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
    """Run greedy workload + timetable synchronously (returns when complete)."""
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


@router.get("/allocations", response_model=list[AllocationRunSummaryRead])
async def list_allocation_runs(
    saved_only: bool = False,
    limit: int = 50,
    session: AsyncSession = Depends(get_db_session),
) -> list[AllocationRunSummaryRead]:
    service = AllocationService()
    return await service.list_runs(session, saved_only=saved_only, limit=limit)


@router.patch("/allocations/{run_id}", response_model=AllocationRunRead)
async def update_allocation_run(
    run_id: int,
    body: AllocationRunUpdateRequest,
    session: AsyncSession = Depends(get_db_session),
) -> AllocationRunRead:
    service = AllocationService()
    try:
        return await service.update_run(session, run_id=run_id, body=body)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


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


@router.post("/allocations/{run_id}/reports/batch-summary", response_model=BatchReportResponse)
async def generate_batch_summary_report(
    run_id: int,
    body: BatchReportRequest,
    session: AsyncSession = Depends(get_db_session),
) -> BatchReportResponse:
    """Generate a markdown department summary for one batch/semester in an allocation run."""
    service = AllocationService()
    run = await service.get_run(session, run_id)
    if run is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Allocation run not found.")
    try:
        return await build_batch_report(
            run,
            batch_code=body.batch_code,
            semester_number=body.semester_number,
            report_mode=body.report_mode,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
