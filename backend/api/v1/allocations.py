"""Allocation run API routes."""

from collections.abc import AsyncIterator

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import Response, StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database.session import get_db_session
from backend.schemas.allocation import (
    AllocationRunRead,
    AllocationRunRequest,
    AllocationRunSummaryRead,
    AllocationRunUpdateRequest,
    BatchSemesterPlan,
)
from backend.schemas.allocation_report import (
    AllBatchesReportRequest,
    AllBatchesReportResponse,
    BatchReportRequest,
    BatchReportResponse,
)
from backend.ai.services.report_service import (
    build_all_batches_report,
    build_batch_report,
    format_sse,
    stream_all_batches_report_events,
    stream_batch_report_events,
)
from backend.services.allocation_service import AllocationService
from backend.services.timetable_export_service import (
    TimetableExportError,
    TimetableExportFormat,
    TimetableExportPack,
    export_filename,
    export_media_type,
    export_timetable_pack,
)
from backend.schemas.timetable_mail import FacultyTimetableMailResult
from backend.services.timetable_mail_service import (
    SmtpNotConfiguredError,
    TimetableMailService,
)

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


@router.get("/allocations/{run_id}/export/timetable/{pack}")
async def export_allocation_timetable(
    run_id: int,
    pack: TimetableExportPack,
    format: TimetableExportFormat = TimetableExportFormat.XLSX,
    session: AsyncSession = Depends(get_db_session),
) -> Response:
    """Download a timetable pack as Excel or PDF (faculty | students | rooms)."""
    service = AllocationService()
    run = await service.get_run(session, run_id)
    if run is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Allocation run not found.")
    try:
        payload = export_timetable_pack(run, pack, format)
    except TimetableExportError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    filename = export_filename(run, pack, format)
    return Response(
        content=payload,
        media_type=export_media_type(format),
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
        },
    )


@router.post(
    "/allocations/{run_id}/email/faculty-timetables",
    response_model=FacultyTimetableMailResult,
)
async def email_faculty_timetables(
    run_id: int,
    session: AsyncSession = Depends(get_db_session),
) -> FacultyTimetableMailResult:
    """Email each faculty member with teaching load their personal timetable PDF."""
    service = AllocationService()
    run = await service.get_run(session, run_id)
    if run is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Allocation run not found.")
    if not run.faculty_timetable_grids:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No faculty timetable grids available for this run.",
        )
    try:
        return await TimetableMailService().send_faculty_timetables(session, run)
    except SmtpNotConfiguredError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


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


@router.post("/allocations/{run_id}/reports/batch-summary/stream")
async def stream_batch_summary_report(
    run_id: int,
    body: BatchReportRequest,
    session: AsyncSession = Depends(get_db_session),
) -> StreamingResponse:
    """Stream a single-batch report as Server-Sent Events (meta / chunk / done)."""
    service = AllocationService()
    run = await service.get_run(session, run_id)
    if run is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Allocation run not found.")

    async def event_source() -> AsyncIterator[str]:
        try:
            async for event in stream_batch_report_events(
                run,
                batch_code=body.batch_code,
                semester_number=body.semester_number,
                report_mode=body.report_mode,
            ):
                yield format_sse(event)
        except ValueError as exc:
            yield format_sse({"type": "error", "message": str(exc)})
        except Exception:
            yield format_sse({"type": "error", "message": "Report streaming failed."})

    return StreamingResponse(
        event_source(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.post("/allocations/{run_id}/reports/all-batches", response_model=AllBatchesReportResponse)
async def generate_all_batches_report(
    run_id: int,
    body: AllBatchesReportRequest,
    session: AsyncSession = Depends(get_db_session),
) -> AllBatchesReportResponse:
    """Generate one combined markdown report covering every batch/semester in a run."""
    service = AllocationService()
    run = await service.get_run(session, run_id)
    if run is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Allocation run not found.")
    try:
        return await build_all_batches_report(run, report_mode=body.report_mode)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.post("/allocations/{run_id}/reports/all-batches/stream")
async def stream_all_batches_report(
    run_id: int,
    body: AllBatchesReportRequest,
    session: AsyncSession = Depends(get_db_session),
) -> StreamingResponse:
    """Stream a combined all-batches report as SSE (cover first, then each batch in order)."""
    service = AllocationService()
    run = await service.get_run(session, run_id)
    if run is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Allocation run not found.")

    async def event_source() -> AsyncIterator[str]:
        try:
            async for event in stream_all_batches_report_events(run, report_mode=body.report_mode):
                yield format_sse(event)
        except Exception:
            yield format_sse({"type": "error", "message": "Combined report streaming failed."})

    return StreamingResponse(
        event_source(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
