"""Unit tests for batch allocation report generation."""

from backend.schemas.allocation import (
    AllocationRunRead,
    BatchSemesterPlanRead,
    PecCourseEnrollmentRead,
    PolicyViolationRead,
    SlotAssignmentRead,
    TimetableEntryRead,
)
from backend.services.allocation_report_service import generate_batch_report


def _assignment(**overrides: object) -> SlotAssignmentRead:
    base = {
        "slot_id": "2023-27-23AM3501-T-S1",
        "course_id": 1,
        "batch_code": "2023-27",
        "course_code": "23AM3501",
        "course_name": "Machine Learning",
        "course_type": "IPCC",
        "kind": "theory",
        "section_indices": [1],
        "weekly_hours": 3,
        "faculty_ids": [1],
        "faculty_names": ["Dr Alpha"],
    }
    base.update(overrides)
    return SlotAssignmentRead(**base)


def _run(**overrides: object) -> AllocationRunRead:
    base = {
        "id": 7,
        "plan_name": "Sem 5 draft",
        "is_saved": True,
        "batch_plans": [
            BatchSemesterPlanRead(
                batch_code="2023-27",
                semester_number=5,
                section_count=4,
                working_days=["monday", "tuesday", "wednesday", "thursday", "friday"],
                pec_enrollments=[
                    PecCourseEnrollmentRead(
                        course_code="23AM3605",
                        course_name="Deep Learning",
                        course_type="PEC 2",
                        student_count=120,
                    ),
                    PecCourseEnrollmentRead(
                        course_code="23AM3606",
                        course_name="Reinforcement Learning",
                        course_type="PEC 2",
                        student_count=0,
                    ),
                ],
            )
        ],
        "batch_codes": ["2023-27"],
        "batch_code": "2023-27",
        "semester_number": 5,
        "section_count": 4,
        "status": "feasible",
        "objective_value": 10,
        "assignment_count": 3,
        "faculty_count": 2,
        "timetable_entry_count": 2,
        "violations": [
            PolicyViolationRead(
                code="MIN_THEORY",
                message="Dr Alpha below minimum theory courses.",
                faculty_id=1,
            )
        ],
        "messages": [],
        "timetable_messages": ["Greedy timetable used."],
        "assignments": [
            _assignment(),
            _assignment(
                slot_id="2023-27-23AM3501-L-S1-B1",
                kind="lab",
                lab_sub_batch="B1",
                weekly_hours=2,
                faculty_ids=[1, 2],
                faculty_names=["Dr Alpha", "Dr Beta"],
            ),
            _assignment(
                slot_id="2023-27-23AM3605-T-S1",
                course_code="23AM3605",
                course_name="Deep Learning",
                course_type="PEC 2",
            ),
        ],
        "faculty_summaries": [],
        "timetable_entries": [
            TimetableEntryRead(
                event_id="e1",
                slot_id="s1",
                batch_code="2023-27",
                course_code="23AM3605",
                course_name="Deep Learning",
                course_type="PEC 2",
                kind="theory",
                section_indices=[1],
                faculty_ids=[2],
                faculty_names=["Dr Beta"],
                day="monday",
                period_numbers=[1],
                period_label="P1",
                room_type="lecture_hall",
                room_name="LH-2",
                start_time="08:30",
                end_time="09:25",
            ),
            TimetableEntryRead(
                event_id="e2",
                slot_id="s2",
                batch_code="2023-27",
                course_code="23AM3501",
                course_name="Machine Learning",
                course_type="IPCC",
                kind="lab",
                section_indices=[1],
                faculty_ids=[1, 2],
                faculty_names=["Dr Alpha", "Dr Beta"],
                day="tuesday",
                period_numbers=[1, 2],
                period_label="P1-P2",
                room_type="laboratory",
                room_name="508",
                start_time="08:30",
                end_time="10:20",
                lab_sub_batch="B1",
            ),
        ],
    }
    base.update(overrides)
    return AllocationRunRead(**base)


def test_generate_batch_report_includes_pec_and_faculty_tables() -> None:
    report = generate_batch_report(_run(), batch_code="2023-27", semester_number=5)

    assert report.facts.unique_courses == 2
    assert report.facts.lab_sessions == 1
    assert report.facts.faculty_assigned == 2
    assert report.facts.pec_rows[0].scheduled is True
    assert report.facts.pec_rows[0].pec_pool_number == 2
    assert report.facts.pec_rows[1].scheduled is False
    assert "Deep Learning" in report.markdown
    assert "Reinforcement Learning" in report.markdown
    assert "### PEC 2" in report.markdown
    assert "Dr Alpha" in report.markdown
    assert "Overall faculty allocation" in report.markdown
    assert "Faculty teaching by batch" in report.markdown
    assert "not per batch" in report.markdown
    assert "Policy warnings" in report.markdown
    assert "Dr Alpha below minimum theory courses." in report.markdown
    # Policy warnings appear once with overall allocation, not as a batch-only section.
    assert report.markdown.count("## Policy warnings") == 1
    assert report.narrative_source == "template"


def test_unknown_batch_semester_rejected() -> None:
    try:
        generate_batch_report(_run(), batch_code="2022-26", semester_number=7)
        raised = False
    except ValueError as exc:
        raised = True
        assert "2022-26" in str(exc)
    assert raised


def test_build_batch_raw_payload_includes_assignments_and_pec_enrollments() -> None:
    from backend.services.allocation_report_service import build_batch_raw_payload

    payload = build_batch_raw_payload(_run(), batch_code="2023-27", semester_number=5)

    assert payload["run_id"] == 7
    assert len(payload["assignments"]) == 3
    assert len(payload["timetable_entries"]) == 2
    batch_plan = payload["batch_plan"]
    assert isinstance(batch_plan, dict)
    assert len(batch_plan["pec_enrollments"]) == 2
    assert payload["workload_status"] == "feasible"


def test_batch_faculty_rows_include_overall_totals_and_aicte_cap() -> None:
    """Batch hours stay batch-scoped; overall hours and AICTE max come from the run summary."""
    from backend.schemas.allocation import FacultyWorkloadSummaryRead

    run = _run(
        faculty_summaries=[
            FacultyWorkloadSummaryRead(
                faculty_id=1,
                full_name="Dr Alpha",
                designation_key="assistant_professor",
                theory_weekly_hours=9,
                lab_weekly_hours=4,
                total_weekly_hours=11,  # 9 + 4/2 teaching load
                theory_course_count=3,
                lab_course_count=1,
                lab_session_count=2,
            ),
            FacultyWorkloadSummaryRead(
                faculty_id=2,
                full_name="Dr Beta",
                designation_key="associate_professor",
                theory_weekly_hours=6,
                lab_weekly_hours=2,
                total_weekly_hours=7,  # 6 + 2/2 teaching load
                theory_course_count=2,
                lab_course_count=1,
                lab_session_count=1,
            ),
        ],
        assignments=[
            _assignment(),  # Dr Alpha: 3 theory hours in this batch
            _assignment(
                slot_id="2023-27-23AM3501-L-S1-B1",
                kind="lab",
                lab_sub_batch="B1",
                weekly_hours=2,
                faculty_ids=[1, 2],
                faculty_names=["Dr Alpha", "Dr Beta"],
            ),
        ],
    )
    report = generate_batch_report(run, batch_code="2023-27", semester_number=5)
    by_id = {row.faculty_id: row for row in report.facts.faculty_rows}

    alpha = by_id[1]
    assert alpha.theory_hours == 3
    assert alpha.lab_hours == 2
    assert alpha.total_hours == 4  # 3 + 2/2 teaching load
    assert alpha.overall_total_hours == 11
    assert alpha.overall_theory_hours == 9
    assert alpha.overall_lab_hours == 4
    assert alpha.max_weekly_hours == 16.0
    assert alpha.total_hours != alpha.overall_total_hours

    beta = by_id[2]
    assert beta.total_hours == 1  # 2 lab contact → 1 teaching load
    assert beta.overall_total_hours == 7
    assert beta.max_weekly_hours == 12.0

    assert "Overall faculty allocation" in report.markdown
    assert "Faculty teaching by batch" in report.markdown
    assert "23AM3501" in report.markdown


def test_consolidated_faculty_table_includes_aicte_max_column() -> None:
    from backend.schemas.allocation import FacultyWorkloadSummaryRead
    from backend.services.allocation_report_service import (
        build_consolidated_faculty_rows,
        render_consolidated_faculty_markdown,
    )

    run = _run(
        faculty_summaries=[
            FacultyWorkloadSummaryRead(
                faculty_id=1,
                full_name="Dr Alpha",
                designation_key="professor",
                theory_weekly_hours=6,
                lab_weekly_hours=0,
                total_weekly_hours=6,
                theory_course_count=2,
                lab_course_count=0,
                lab_session_count=0,
            ),
        ],
    )
    rows = build_consolidated_faculty_rows(run)
    assert rows[0].max_weekly_hours == 8.0
    assert rows[0].teaching_assignments
    assert rows[0].teaching_assignments[0].course_code == "23AM3501"

    md = render_consolidated_faculty_markdown(
        rows,
        violation_messages=["Dr Alpha below minimum theory courses."],
    )
    assert "Overall faculty allocation" in md
    assert "Faculty teaching by batch" in md
    assert "AICTE max h" in md
    assert "not per batch" in md
    assert "**2023-27**" in md
    assert "Machine Learning" in md
    assert "## Policy warnings" in md
    assert "Dr Alpha below minimum theory courses." in md
