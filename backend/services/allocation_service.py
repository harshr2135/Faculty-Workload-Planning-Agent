"""Orchestrate workload allocation and timetable scheduling."""

from __future__ import annotations

import logging
from dataclasses import asdict

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.core.domain.aiml_config import DEPARTMENT_NAME, WEEKDAYS_MON_FRI
from backend.core.domain.course_type_config import is_pec_course_type
from backend.core.domain.course_type_config import requires_room_allocation
from backend.core.domain.pec_config import delivery_requires_lecture_hall
from backend.core.domain.batch_planning import default_batch_plans
from backend.core.domain.policy_config import LAB_FACULTY_PER_SESSION, UNLIMITED_MAX_WEEKLY_HOURS, resolve_designation_key
from backend.models import (
    AllocationRun,
    Classroom,
    Course,
    Department,
    DesignationWorkloadPolicy,
    FacultyMember,
    Laboratory,
    LectureHall,
    Semester,
    StudentBatch,
    TimeSlot,
)
from backend.optimization.engine.greedy_workload_allocator import GreedyWorkloadAllocator
from backend.optimization.engine.timetable_cpsat_solver import TimetableCpsatSolver
from backend.optimization.models.problem_definition import (
    BatchPlanInput,
    CourseInput,
    FacultyInput,
    WorkloadProblem,
)
from backend.optimization.models.solution import OptimizationSolution, SolverStatus
from backend.optimization.models.timetable_problem import (
    PeriodInfo,
    RoomInput,
    RoomKind,
    TimetableProblem,
    TimetableSolverConfig,
)
from backend.optimization.models.timetable_solution import TimetableSolution
from backend.optimization.preprocessing.eligibility import (
    build_course_eligibility,
    fallback_faculty_ids_from_roster,
)
from backend.optimization.preprocessing.period_utils import teaching_period_numbers
from backend.optimization.preprocessing.schedule_event_builder import (
    build_consecutive_block_index,
    build_schedule_events,
)
from backend.optimization.preprocessing.slot_builder import build_assignment_slots
from backend.schemas.allocation import (
    AllocationRunRead,
    AllocationRunSummaryRead,
    AllocationRunUpdateRequest,
    BatchSemesterPlan,
    BatchSemesterPlanRead,
    FacultyTimetableGridRead,
    FacultyWorkloadSummaryRead,
    PecCourseEnrollmentRead,
    PolicyViolationRead,
    RoomTimetableGridRead,
    SectionTimetableGridRead,
    SlotAssignmentRead,
    TimetableEntryRead,
    TimetableGridRead,
)
from backend.services.allocation_edit_service import (
    apply_faculty_names,
    load_faculty_lookup,
    recompute_faculty_summaries,
    sync_timetable_entry_faculty,
    touch_plan_metadata,
)
from backend.services.timetable_grid_service import (
    build_faculty_timetable_grids,
    build_room_timetable_grids,
    build_section_timetable_grids,
    build_timetable_grid,
)

DAY_ORDER = ("monday", "tuesday", "wednesday", "thursday", "friday")
logger = logging.getLogger(__name__)


class AllocationService:
    async def run_allocation(
        self,
        session: AsyncSession,
        batch_plans: list[BatchSemesterPlan] | None = None,
        max_time_seconds: float = 120.0,
        schedule_timetable: bool = True,
    ) -> AllocationRunRead:
        """Greedy workload + CP-SAT timetable (first feasible solution)."""
        resolved_plans = await self._resolve_batch_plans(session, batch_plans)
        problem, primary_batch, primary_semester = await self._build_problem(
            session,
            batch_plans=resolved_plans,
        )

        workload_solution = GreedyWorkloadAllocator().allocate(problem)

        timetable_solution: TimetableSolution | None = None
        if (
            schedule_timetable
            and workload_solution.status in (SolverStatus.OPTIMAL, SolverStatus.FEASIBLE)
        ):
            timetable_problem = await self._build_timetable_problem(
                session,
                batch_plans=problem.batch_plans,
                workload_solution=workload_solution,
            )
            timetable_config = TimetableSolverConfig(
                max_time_seconds=max_time_seconds,
                stop_after_first_solution=True,
            )
            timetable_solution = TimetableCpsatSolver().solve(
                timetable_problem,
                config=timetable_config,
            )

        run = AllocationRun(
            department_id=primary_batch.department_id,
            batch_id=primary_batch.id,
            semester_id=primary_semester.id,
            status=workload_solution.status.value,
            objective_value=workload_solution.objective_value,
            solution=_solution_to_dict(
                problem,
                workload_solution,
                timetable_solution,
                resolved_plans=resolved_plans,
            ),
        )
        session.add(run)
        await session.flush()

        return _to_read_model(
            run,
            problem,
            workload_solution,
            timetable_solution,
            resolved_plans=resolved_plans,
        )

    async def get_run(self, session: AsyncSession, run_id: int) -> AllocationRunRead | None:
        result = await session.execute(
            select(AllocationRun)
            .where(AllocationRun.id == run_id)
            .options(
                selectinload(AllocationRun.batch),
                selectinload(AllocationRun.semester).selectinload(Semester.academic_year_level),
            )
        )
        run = result.scalar_one_or_none()
        if run is None:
            return None
        if run.solution is None:
            return None
        return _read_from_stored(run)

    async def list_runs(
        self,
        session: AsyncSession,
        *,
        saved_only: bool = False,
        limit: int = 50,
    ) -> list[AllocationRunSummaryRead]:
        result = await session.execute(
            select(AllocationRun)
            .order_by(AllocationRun.created_at.desc())
            .limit(limit)
            .options(
                selectinload(AllocationRun.batch),
                selectinload(AllocationRun.semester).selectinload(Semester.academic_year_level),
            )
        )
        summaries: list[AllocationRunSummaryRead] = []
        for run in result.scalars().all():
            payload = run.solution or {}
            is_saved = bool(payload.get("is_saved"))
            if saved_only and not is_saved:
                continue
            batch_plans = _batch_plans_from_payload(payload)
            batch_codes = [plan.batch_code for plan in batch_plans] or [run.batch.batch_code]
            summaries.append(
                AllocationRunSummaryRead(
                    id=run.id,
                    plan_name=_plan_name(payload, run.id),
                    is_saved=is_saved,
                    batch_codes=batch_codes,
                    batch_label=_batch_label(batch_plans, batch_codes),
                    status=run.status,
                    timetable_status=payload.get("timetable_status"),
                    assignment_count=len(payload.get("assignments", [])),
                    created_at=run.created_at.isoformat() if run.created_at else None,
                    updated_at=payload.get("updated_at")
                    or (run.updated_at.isoformat() if run.updated_at else None),
                )
            )
        return summaries

    async def update_run(
        self,
        session: AsyncSession,
        run_id: int,
        body: AllocationRunUpdateRequest,
    ) -> AllocationRunRead:
        result = await session.execute(
            select(AllocationRun)
            .where(AllocationRun.id == run_id)
            .options(
                selectinload(AllocationRun.batch),
                selectinload(AllocationRun.semester).selectinload(Semester.academic_year_level),
            )
        )
        run = result.scalar_one_or_none()
        if run is None or run.solution is None:
            msg = "Allocation run not found."
            raise ValueError(msg)

        payload = dict(run.solution)
        faculty_by_id = await load_faculty_lookup(session)

        if body.assignments is not None:
            assignment_dicts = [item.model_dump() for item in body.assignments]
            assignment_dicts = apply_faculty_names(assignment_dicts, faculty_by_id)
            payload["assignments"] = assignment_dicts
            payload["faculty_summaries"] = recompute_faculty_summaries(
                assignment_dicts,
                faculty_by_id,
            )
            payload["timetable_entries"] = sync_timetable_entry_faculty(
                payload.get("timetable_entries", []),
                assignment_dicts,
            )

        payload = touch_plan_metadata(
            payload,
            plan_name=body.plan_name,
            is_saved=body.is_saved,
        )
        run.solution = payload
        await session.flush()
        return _read_from_stored(run)

    async def _resolve_batch_plans(
        self,
        session: AsyncSession,
        batch_plans: list[BatchSemesterPlan] | None,
    ) -> list[BatchSemesterPlan]:
        if batch_plans:
            return batch_plans

        dept = await session.scalar(select(Department).where(Department.name == DEPARTMENT_NAME))
        if dept is None:
            raise ValueError(f"Department '{DEPARTMENT_NAME}' not found.")

        return [
            BatchSemesterPlan(batch_code=code, semester_number=semester)
            for code, semester in default_batch_plans()
        ]

    async def _get_semester(
        self,
        session: AsyncSession,
        department_id: int,
        semester_number: int,
    ) -> Semester:
        semester = await session.scalar(
            select(Semester)
            .where(
                Semester.department_id == department_id,
                Semester.semester_number == semester_number,
            )
            .options(selectinload(Semester.academic_year_level))
        )
        if semester is None:
            raise ValueError(f"Semester {semester_number} not configured.")
        return semester

    async def _build_timetable_problem(
        self,
        session: AsyncSession,
        batch_plans: tuple[BatchPlanInput, ...],
        workload_solution: OptimizationSolution,
    ) -> TimetableProblem:
        dept = await session.scalar(select(Department).where(Department.name == DEPARTMENT_NAME))
        if dept is None:
            raise ValueError(f"Department '{DEPARTMENT_NAME}' not found.")

        classrooms = list(
            (
                await session.execute(
                    select(Classroom).where(Classroom.department_id == dept.id).order_by(Classroom.room_number)
                )
            ).scalars().all()
        )
        laboratories = list(
            (
                await session.execute(
                    select(Laboratory).where(Laboratory.department_id == dept.id).order_by(Laboratory.room_number)
                )
            ).scalars().all()
        )
        lecture_halls = list(
            (await session.execute(select(LectureHall).order_by(LectureHall.name))).scalars().all()
        )
        time_slots = list(
            (
                await session.execute(
                    select(TimeSlot)
                    .where(TimeSlot.department_id == dept.id, TimeSlot.slot_type == "teaching")
                    .order_by(TimeSlot.sort_order)
                )
            ).scalars().all()
        )

        events = build_schedule_events(workload_solution.assignments)
        max_duration = max((event.duration_periods for event in events), default=1)

        period_info = tuple(
            PeriodInfo(
                period_number=slot.period_number or 0,
                label=slot.label,
                start_time=slot.start_time.strftime("%H:%M"),
                end_time=slot.end_time.strftime("%H:%M"),
            )
            for slot in time_slots
            if slot.period_number is not None
        )

        return TimetableProblem(
            batch_codes=tuple(plan.batch_code for plan in batch_plans),
            working_days=_union_working_days(batch_plans),
            teaching_periods=tuple(teaching_period_numbers()),
            period_info=period_info,
            classrooms=tuple(
                RoomInput(id=room.id, name=room.room_number, kind=RoomKind.CLASSROOM)
                for room in classrooms
            ),
            lecture_halls=tuple(
                RoomInput(id=hall.id, name=hall.name, kind=RoomKind.LECTURE_HALL)
                for hall in lecture_halls
            ),
            laboratories=tuple(
                RoomInput(id=lab.id, name=lab.room_number, kind=RoomKind.LABORATORY)
                for lab in laboratories
            ),
            events=tuple(events),
            consecutive_blocks=build_consecutive_block_index(max_duration),
        )

    async def _build_problem(
        self,
        session: AsyncSession,
        batch_plans: list[BatchSemesterPlan],
    ) -> tuple[WorkloadProblem, StudentBatch, Semester]:
        if not batch_plans:
            raise ValueError("At least one batch semester plan is required.")

        dept = await session.scalar(select(Department).where(Department.name == DEPARTMENT_NAME))
        if dept is None:
            raise ValueError(f"Department '{DEPARTMENT_NAME}' not found.")

        plan_inputs: list[BatchPlanInput] = []
        course_inputs: list[CourseInput] = []
        primary_batch: StudentBatch | None = None
        primary_semester: Semester | None = None

        for index, plan in enumerate(batch_plans):
            batch = await session.scalar(
                select(StudentBatch).where(
                    StudentBatch.department_id == dept.id,
                    StudentBatch.batch_code == plan.batch_code,
                )
            )
            if batch is None:
                raise ValueError(f"Student batch '{plan.batch_code}' not found.")

            semester = await self._get_semester(session, dept.id, plan.semester_number)
            year_level = semester.academic_year_level
            working_days = tuple(year_level.working_days)
            section_count = year_level.section_count

            plan_inputs.append(
                BatchPlanInput(
                    batch_code=plan.batch_code,
                    semester_number=plan.semester_number,
                    section_count=section_count,
                    working_days=working_days,
                )
            )

            if index == 0:
                primary_batch = batch
                primary_semester = semester

            course_rows = await session.execute(
                select(Course)
                .where(
                    Course.department_id == dept.id,
                    Course.batch_id == batch.id,
                    Course.semester_id == semester.id,
                )
                .options(selectinload(Course.batch))
                .order_by(Course.course_code)
            )
            batch_courses = list(course_rows.scalars().all())
            if not batch_courses:
                raise ValueError(
                    f"No courses for batch {plan.batch_code} semester {plan.semester_number}. "
                    "Import Courses.xlsx first."
                )

            pec_counts = _pec_enrollment_counts(plan)

            for course in batch_courses:
                if not _include_course_for_plan(course, plan):
                    continue
                student_count = pec_counts.get(course.course_code.strip().upper(), 0)
                needs_lecture_hall = delivery_requires_lecture_hall(
                    course.course_type,
                    student_count,
                )
                if not requires_room_allocation(course.name):
                    needs_lecture_hall = False
                course_inputs.append(
                    CourseInput(
                        id=course.id,
                        batch_code=course.batch.batch_code if course.batch else plan.batch_code,
                        semester_number=plan.semester_number,
                        section_count=section_count,
                        working_days=working_days,
                        course_code=course.course_code,
                        name=course.name,
                        course_type=course.course_type,
                        lectures_per_week=course.lectures_per_week,
                        practical_hours=course.practical_hours,
                        requires_lecture_hall=needs_lecture_hall,
                    )
                )

        faculty_rows = await session.execute(
            select(FacultyMember)
            .where(FacultyMember.department_id == dept.id)
            .options(selectinload(FacultyMember.specializations))
            .order_by(FacultyMember.full_name)
        )
        faculty_members = list(faculty_rows.scalars().unique().all())

        policy_rows = await session.execute(
            select(DesignationWorkloadPolicy).where(
                DesignationWorkloadPolicy.department_id == dept.id
            )
        )
        policies = {row.designation_key: row for row in policy_rows.scalars().all()}

        faculty_inputs: list[FacultyInput] = []
        faculty_specs: dict[int, list[str]] = {}
        for member in faculty_members:
            designation_key = resolve_designation_key(member.designation)
            policy = policies.get(designation_key or "")
            faculty_specs[member.id] = [spec.name for spec in member.specializations]
            faculty_inputs.append(
                FacultyInput(
                    id=member.id,
                    full_name=member.full_name,
                    designation_key=designation_key,
                    designation_label=member.designation,
                    min_weekly_hours=policy.min_weekly_hours if policy else 0.0,
                    max_weekly_hours=UNLIMITED_MAX_WEEKLY_HOURS,
                    min_theory_courses=policy.min_theory_courses if policy else 0,
                    min_lab_courses=policy.min_lab_courses if policy else 0,
                    min_lab_sessions=policy.min_lab_sessions if policy else None,
                    max_lab_sessions=None,
                )
            )

        fallback_ids = fallback_faculty_ids_from_roster(faculty_inputs)
        eligible, matched, fallback_flags = build_course_eligibility(
            course_inputs,
            faculty_inputs,
            faculty_specs,
            fallback_ids,
        )

        slots = build_assignment_slots(
            course_inputs,
            eligibility=eligible,
            matched_ids=matched,
            fallback_flags=fallback_flags,
        )

        problem = WorkloadProblem(
            batch_plans=tuple(plan_inputs),
            lab_faculty_per_session=LAB_FACULTY_PER_SESSION,
            faculty=tuple(faculty_inputs),
            courses=tuple(course_inputs),
            slots=tuple(slots),
        )
        assert primary_batch is not None and primary_semester is not None
        return problem, primary_batch, primary_semester


def _pec_enrollment_counts(plan: BatchSemesterPlan) -> dict[str, int]:
    return {
        entry.course_code.strip().upper(): entry.student_count
        for entry in plan.pec_enrollments
    }


def _include_course_for_plan(course: Course, plan: BatchSemesterPlan) -> bool:
    """Non-PEC courses always run; PEC electives only when student_count > 0."""
    if not is_pec_course_type(course.course_type):
        return True
    if not plan.pec_enrollments:
        return True
    return _pec_enrollment_counts(plan).get(course.course_code.strip().upper(), 0) > 0


def _pec_enrollment_reads(
    batch_code: str,
    semester_number: int,
    resolved_plans: list[BatchSemesterPlan] | None,
) -> list[PecCourseEnrollmentRead]:
    if not resolved_plans:
        return []
    for plan in resolved_plans:
        if plan.batch_code == batch_code and plan.semester_number == semester_number:
            return [
                PecCourseEnrollmentRead(
                    course_code=entry.course_code.strip().upper(),
                    student_count=entry.student_count,
                )
                for entry in plan.pec_enrollments
            ]
    return []


def _union_working_days(batch_plans: tuple[BatchPlanInput, ...]) -> tuple[str, ...]:
    ordered: list[str] = []
    seen: set[str] = set()
    for day in DAY_ORDER:
        if any(day in plan.working_days for plan in batch_plans) and day not in seen:
            ordered.append(day)
            seen.add(day)
    return tuple(ordered) if ordered else tuple(WEEKDAYS_MON_FRI)


def _batch_plan_reads(
    problem: WorkloadProblem,
    resolved_plans: list[BatchSemesterPlan] | None = None,
) -> list[BatchSemesterPlanRead]:
    return [
        BatchSemesterPlanRead(
            batch_code=plan.batch_code,
            semester_number=plan.semester_number,
            section_count=plan.section_count,
            working_days=list(plan.working_days),
            pec_enrollments=_pec_enrollment_reads(
                plan.batch_code,
                plan.semester_number,
                resolved_plans,
            ),
        )
        for plan in problem.batch_plans
    ]


def _batch_plans_for_storage(
    problem: WorkloadProblem,
    resolved_plans: list[BatchSemesterPlan] | None = None,
) -> list[dict]:
    return [
        {
            "batch_code": plan.batch_code,
            "semester_number": plan.semester_number,
            "section_count": plan.section_count,
            "working_days": list(plan.working_days),
            "pec_enrollments": [
                entry.model_dump()
                for entry in _pec_enrollment_reads(
                    plan.batch_code,
                    plan.semester_number,
                    resolved_plans,
                )
            ],
        }
        for plan in problem.batch_plans
    ]


def _solution_to_dict(
    problem: WorkloadProblem,
    workload: OptimizationSolution,
    timetable: TimetableSolution | None,
    resolved_plans: list[BatchSemesterPlan] | None = None,
) -> dict:
    return {
        "run_state": "completed",
        "batch_plans": _batch_plans_for_storage(problem, resolved_plans),
        "batch_codes": [plan.batch_code for plan in problem.batch_plans],
        "status": workload.status.value,
        "objective_value": workload.objective_value,
        "messages": workload.messages,
        "assignments": [asdict(item) for item in workload.assignments],
        "faculty_summaries": [asdict(item) for item in workload.faculty_summaries],
        "violations": [asdict(item) for item in workload.violations],
        "timetable_status": timetable.status.value if timetable else None,
        "timetable_messages": timetable.messages if timetable else [],
        "timetable_entries": [asdict(entry) for entry in timetable.entries] if timetable else [],
        "plan_name": None,
        "is_saved": False,
        "updated_at": None,
    }


def _plan_name(payload: dict, run_id: int) -> str:
    name = (payload.get("plan_name") or "").strip()
    if name:
        return name
    return f"Run #{run_id}"


def _batch_label(batch_plans: list[BatchSemesterPlanRead], batch_codes: list[str]) -> str:
    if batch_plans:
        return " · ".join(
            f"{plan.batch_code} (sem {plan.semester_number})" for plan in batch_plans
        )
    return " · ".join(batch_codes)


def _metadata_from_payload(payload: dict, run_id: int) -> tuple[str | None, bool, str | None]:
    plan_name = (payload.get("plan_name") or "").strip() or None
    is_saved = bool(payload.get("is_saved"))
    updated_at = payload.get("updated_at")
    if not plan_name and is_saved:
        plan_name = _plan_name(payload, run_id)
    return plan_name, is_saved, updated_at


def _timetable_entries_from_solution(
    timetable: TimetableSolution | None,
) -> list[TimetableEntryRead]:
    if timetable is None:
        return []
    return [TimetableEntryRead(**asdict(entry)) for entry in timetable.entries]


def _timetable_views(
    timetable_entries: list[TimetableEntryRead],
    faculty_summaries: list[FacultyWorkloadSummaryRead],
    batch_plans: list[BatchSemesterPlanRead],
) -> tuple[
    TimetableGridRead | None,
    list[FacultyTimetableGridRead],
    list[SectionTimetableGridRead],
    list[RoomTimetableGridRead],
    list[RoomTimetableGridRead],
]:
    section_grids = build_section_timetable_grids(timetable_entries, batch_plans)
    classroom_grids = build_room_timetable_grids(timetable_entries, "classroom")
    laboratory_grids = build_room_timetable_grids(timetable_entries, "laboratory")
    if not timetable_entries:
        return None, [], section_grids, classroom_grids, laboratory_grids
    grid = build_timetable_grid(timetable_entries)
    faculty_grids = build_faculty_timetable_grids(timetable_entries, faculty_summaries)
    return grid, faculty_grids, section_grids, classroom_grids, laboratory_grids


def _batch_plans_from_payload(payload: dict) -> list[BatchSemesterPlanRead]:
    raw_plans = payload.get("batch_plans", [])
    if raw_plans:
        return [BatchSemesterPlanRead.model_validate(plan) for plan in raw_plans]
    batch_codes = payload.get("batch_codes") or []
    semester_number = payload.get("semester_number", 0)
    return [
        BatchSemesterPlanRead(
            batch_code=code,
            semester_number=semester_number,
            section_count=payload.get("section_count", 0),
            working_days=[],
        )
        for code in batch_codes
    ]


def _to_read_model(
    run: AllocationRun,
    problem: WorkloadProblem,
    workload: OptimizationSolution,
    timetable: TimetableSolution | None,
    resolved_plans: list[BatchSemesterPlan] | None = None,
) -> AllocationRunRead:
    timetable_entries = _timetable_entries_from_solution(timetable)
    faculty_summaries = [
        FacultyWorkloadSummaryRead(**asdict(s)) for s in workload.faculty_summaries
    ]
    batch_plans = _batch_plan_reads(problem, resolved_plans)
    timetable_grid, faculty_timetable_grids, section_timetable_grids, classroom_timetable_grids, laboratory_timetable_grids = _timetable_views(
        timetable_entries,
        faculty_summaries,
        batch_plans,
    )
    batch_codes = [plan.batch_code for plan in batch_plans]
    first_plan = batch_plans[0] if batch_plans else None
    return AllocationRunRead(
        id=run.id,
        plan_name=None,
        is_saved=False,
        batch_plans=batch_plans,
        batch_codes=batch_codes,
        batch_code=batch_codes[0] if batch_codes else "",
        semester_number=first_plan.semester_number if first_plan else None,
        section_count=first_plan.section_count if first_plan else None,
        status=workload.status.value,
        run_state="completed",
        timetable_status=timetable.status.value if timetable else None,
        objective_value=workload.objective_value,
        assignment_count=len(workload.assignments),
        faculty_count=len(workload.faculty_summaries),
        timetable_entry_count=len(timetable_entries),
        violations=[PolicyViolationRead(**asdict(v)) for v in workload.violations],
        messages=workload.messages,
        timetable_messages=timetable.messages if timetable else [],
        assignments=[SlotAssignmentRead(**asdict(a)) for a in workload.assignments],
        faculty_summaries=faculty_summaries,
        timetable_entries=timetable_entries,
        timetable_grid=timetable_grid,
        faculty_timetable_grids=faculty_timetable_grids,
        section_timetable_grids=section_timetable_grids,
        classroom_timetable_grids=classroom_timetable_grids,
        laboratory_timetable_grids=laboratory_timetable_grids,
    )


def _read_from_stored(run: AllocationRun) -> AllocationRunRead:
    payload = run.solution or {}
    run_state = payload.get("run_state")
    if run.status == "failed":
        plan_reads = _batch_plans_from_payload(payload)
        batch_codes = [plan.batch_code for plan in plan_reads]
        first_plan = plan_reads[0] if plan_reads else None
        return AllocationRunRead(
            id=run.id,
            batch_plans=plan_reads,
            batch_codes=batch_codes,
            batch_code=batch_codes[0] if batch_codes else run.batch.batch_code,
            semester_number=first_plan.semester_number if first_plan else run.semester.semester_number,
            section_count=first_plan.section_count if first_plan else None,
            status="failed",
            run_state="failed",
            error_message=payload.get("error_message"),
            objective_value=run.objective_value,
            assignment_count=0,
            faculty_count=0,
            timetable_entry_count=0,
            messages=[payload.get("error_message", "Allocation run failed.")],
        )

    raw_plans = payload.get("batch_plans", [])
    if raw_plans:
        batch_plans = [BatchSemesterPlanRead.model_validate(plan) for plan in raw_plans]
    else:
        batch_codes = payload.get("batch_codes") or [run.batch.batch_code]
        semester_number = run.semester.semester_number
        batch_plans = [
            BatchSemesterPlanRead(
                batch_code=code,
                semester_number=semester_number,
                section_count=payload.get("section_count", 0),
                working_days=list(run.semester.academic_year_level.working_days),
            )
            for code in batch_codes
        ]
    batch_codes = [plan.batch_code for plan in batch_plans]
    first_plan = batch_plans[0] if batch_plans else None
    timetable_entries = [
        TimetableEntryRead.model_validate(entry)
        for entry in payload.get("timetable_entries", [])
    ]
    faculty_summaries = [
        FacultyWorkloadSummaryRead.model_validate(s)
        for s in payload.get("faculty_summaries", [])
    ]
    timetable_grid, faculty_timetable_grids, section_timetable_grids, classroom_timetable_grids, laboratory_timetable_grids = _timetable_views(
        timetable_entries,
        faculty_summaries,
        batch_plans,
    )
    plan_name, is_saved, updated_at = _metadata_from_payload(payload, run.id)
    return AllocationRunRead(
        id=run.id,
        plan_name=plan_name,
        is_saved=is_saved,
        batch_plans=batch_plans,
        batch_codes=batch_codes,
        batch_code=batch_codes[0] if batch_codes else run.batch.batch_code,
        semester_number=first_plan.semester_number if first_plan else run.semester.semester_number,
        section_count=first_plan.section_count if first_plan else payload.get("section_count"),
        status=run.status,
        run_state=run_state or "completed",
        error_message=payload.get("error_message"),
        started_at=payload.get("started_at"),
        updated_at=updated_at
        or (run.updated_at.isoformat() if run.updated_at else None),
        timetable_status=payload.get("timetable_status"),
        objective_value=run.objective_value,
        assignment_count=len(payload.get("assignments", [])),
        faculty_count=len(payload.get("faculty_summaries", [])),
        timetable_entry_count=len(timetable_entries),
        violations=[PolicyViolationRead.model_validate(v) for v in payload.get("violations", [])],
        messages=payload.get("messages", []),
        timetable_messages=payload.get("timetable_messages", []),
        assignments=[
            SlotAssignmentRead.model_validate(a) for a in payload.get("assignments", [])
        ],
        faculty_summaries=faculty_summaries,
        timetable_entries=timetable_entries,
        timetable_grid=timetable_grid,
        faculty_timetable_grids=faculty_timetable_grids,
        section_timetable_grids=section_timetable_grids,
        classroom_timetable_grids=classroom_timetable_grids,
        laboratory_timetable_grids=laboratory_timetable_grids,
    )
