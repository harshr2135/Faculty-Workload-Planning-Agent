"""Faculty API routes."""

from io import BytesIO

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database.session import get_db_session
from backend.schemas.faculty import FacultyImportResult, FacultyMemberRead
from backend.services.faculty_import_service import FacultyImportService
from backend.services.faculty_service import FacultyService

router = APIRouter(prefix="/faculty", tags=["faculty"])


@router.post("/import", response_model=FacultyImportResult)
async def import_faculty_excel(
    file: UploadFile = File(...),
    session: AsyncSession = Depends(get_db_session),
) -> FacultyImportResult:
    """Upload an Excel (.xlsx) file and import faculty records."""
    if not file.filename or not file.filename.lower().endswith(".xlsx"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only .xlsx files are supported.",
        )

    try:
        content = await file.read()
        service = FacultyImportService()
        return await service.import_from_excel(session, source=BytesIO(content))
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc


@router.get("", response_model=list[FacultyMemberRead])
async def list_faculty(
    session: AsyncSession = Depends(get_db_session),
) -> list[FacultyMemberRead]:
    """List imported faculty members."""
    service = FacultyService()
    faculty_members = await service.list_faculty(session)
    return [
        FacultyMemberRead(
            id=member.id,
            serial_number=member.serial_number,
            full_name=member.full_name,
            designation=member.designation,
            department=member.department.name,
            email=member.email,
            phone=member.phone,
            cabin_number=member.cabin_number,
            specializations=member.specializations,
        )
        for member in faculty_members
    ]
