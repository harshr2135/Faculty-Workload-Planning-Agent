"""Course, classroom, laboratory, and semester API routes."""

from io import BytesIO

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.domain.batch_planning import default_planning_semester
from backend.database.session import get_db_session
from backend.schemas.course import (
    AcademicYearLevelRead,
    ClassroomRead,
    CourseImportResult,
    CourseRead,
    LaboratoryRead,
    LectureHallRead,
    SemesterRead,
    StudentBatchRead,
)
from backend.schemas.specialization_match import CourseSpecializationMatchRead, MatchedFacultyRead
from backend.services.course_import_service import CourseImportService
from backend.services.course_service import CourseService
from backend.services.department_seed_service import DepartmentSeedService
from backend.services.specialization_match_service import SpecializationMatchService

router = APIRouter(tags=["courses"])


@router.post("/courses/import", response_model=CourseImportResult)
async def import_courses_excel(
    file: UploadFile = File(...),
    replace: bool = Query(default=False, description="Replace entire course catalog before import"),
    session: AsyncSession = Depends(get_db_session),
) -> CourseImportResult:
    if not file.filename or not file.filename.lower().endswith(".xlsx"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only .xlsx files are supported.",
        )
    try:
        content = await file.read()
        service = CourseImportService()
        return await service.import_from_excel(
            session,
            source=BytesIO(content),
            replace_catalog=replace,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.get("/courses", response_model=list[CourseRead])
async def list_courses(
    semester: int | None = Query(default=None, ge=1, le=12),
    batch: str | None = Query(default=None, description="Student batch code, e.g. 2023-27"),
    session: AsyncSession = Depends(get_db_session),
) -> list[CourseRead]:
    service = CourseService()
    courses = await service.list_courses(
        session,
        semester_number=semester,
        batch_code=batch,
    )
    return [
        CourseRead(
            id=course.id,
            course_code=course.course_code,
            name=course.name,
            batch_code=course.batch.batch_code if course.batch else "",
            course_type=course.course_type or "",
            credits=course.credits,
            semester_number=course.semester.semester_number,
            year_level=course.semester.academic_year_level.year_level,
            year_label=course.semester.academic_year_level.label,
            section_count=course.semester.academic_year_level.section_count,
            lectures_per_week=course.lectures_per_week,
            practical_hours=course.practical_hours,
            has_lab=course.has_lab,
            requires_lecture_hall=course.requires_lecture_hall,
        )
        for course in courses
    ]


@router.get(
    "/courses/specialization-matches",
    response_model=list[CourseSpecializationMatchRead],
)
async def list_course_specialization_matches(
    semester: int | None = Query(default=None, ge=1, le=12),
    batch: str | None = Query(default=None, description="Student batch code, e.g. 2023-27"),
    session: AsyncSession = Depends(get_db_session),
) -> list[CourseSpecializationMatchRead]:
    """Preview inferred course keywords and faculty with similar specializations."""
    service = SpecializationMatchService()
    matches = await service.get_course_matches(
        session,
        semester_number=semester,
        batch_code=batch,
    )
    return [
        CourseSpecializationMatchRead(
            course_id=m.course_id,
            course_code=m.course_code,
            course_name=m.course_name,
            inferred_keywords=m.inferred_keywords,
            matched_faculty=[MatchedFacultyRead.model_validate(f) for f in m.matched_faculty],
            fallback_required=m.fallback_required,
        )
        for m in matches
    ]


@router.get("/lecture-halls", response_model=list[LectureHallRead])
async def list_lecture_halls(
    session: AsyncSession = Depends(get_db_session),
) -> list[LectureHallRead]:
    service = CourseService()
    return await service.list_lecture_halls(session)


@router.get("/student-batches", response_model=list[StudentBatchRead])
async def list_student_batches(
    session: AsyncSession = Depends(get_db_session),
) -> list[StudentBatchRead]:
    service = CourseService()
    batches = await service.list_student_batches(session)
    return [
        StudentBatchRead(
            id=batch.id,
            batch_code=batch.batch_code,
            default_planning_semester=default_planning_semester(batch.batch_code),
        )
        for batch in batches
    ]


@router.get("/classrooms", response_model=list[ClassroomRead])
async def list_classrooms(
    session: AsyncSession = Depends(get_db_session),
) -> list[ClassroomRead]:
    service = CourseService()
    return await service.list_classrooms(session)


@router.get("/laboratories", response_model=list[LaboratoryRead])
async def list_laboratories(
    session: AsyncSession = Depends(get_db_session),
) -> list[LaboratoryRead]:
    service = CourseService()
    return await service.list_laboratories(session)


@router.get("/semesters", response_model=list[SemesterRead])
async def list_semesters(
    session: AsyncSession = Depends(get_db_session),
) -> list[SemesterRead]:
    service = CourseService()
    semesters = await service.list_semesters(session)
    return [
        SemesterRead(
            id=semester.id,
            semester_number=semester.semester_number,
            year_level=semester.academic_year_level.year_level,
            year_label=semester.academic_year_level.label,
            section_count=semester.academic_year_level.section_count,
            working_days=semester.academic_year_level.working_days,
        )
        for semester in semesters
    ]


@router.get("/academic-year-levels", response_model=list[AcademicYearLevelRead])
async def list_academic_year_levels(
    session: AsyncSession = Depends(get_db_session),
) -> list[AcademicYearLevelRead]:
    service = CourseService()
    return await service.list_year_levels(session)


@router.post("/department/seed-aiml")
async def seed_aiml_department(
    session: AsyncSession = Depends(get_db_session),
) -> dict[str, int]:
    """Seed AIML classrooms, laboratories, lecture halls, batches, and year-level rules."""
    service = DepartmentSeedService()
    return await service.seed_aiml_resources(session)
