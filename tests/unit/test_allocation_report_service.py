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
    assert "Policy warnings" in report.markdown
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
