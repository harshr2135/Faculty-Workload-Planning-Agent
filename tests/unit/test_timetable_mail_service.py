"""Unit tests for faculty timetable email delivery."""

from email.message import EmailMessage
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest

from backend.config.settings import Settings
from backend.schemas.allocation import (
    AllocationRunRead,
    BatchSemesterPlanRead,
    FacultyTimetableGridRead,
    FacultyWorkloadSummaryRead,
    TimetableEntryRead,
)
from backend.schemas.timetable_mail import FacultyTimetableMailStatus
from backend.services.timetable_export_service import (
    TimetableExportError,
    export_single_faculty_pdf,
    single_faculty_pdf_filename,
)
from backend.services.timetable_grid_service import (
    build_faculty_timetable_grids,
    build_timetable_grid,
)
from backend.services.timetable_mail_service import (
    SmtpNotConfiguredError,
    TimetableMailService,
)


def _entry(**overrides: object) -> TimetableEntryRead:
    payload = {
        "event_id": "evt-1",
        "slot_id": "slot-1",
        "batch_code": "2023-27",
        "course_code": "AIML301",
        "course_name": "Machine Learning",
        "course_type": "PCC",
        "kind": "theory",
        "section_indices": [1],
        "faculty_ids": [10],
        "faculty_names": ["Dr A"],
        "day": "monday",
        "period_numbers": [1],
        "period_label": "P1",
        "room_type": "classroom",
        "room_name": "424",
        "start_time": "08:30",
        "end_time": "09:25",
    }
    payload.update(overrides)
    return TimetableEntryRead(**payload)


def _run_with_faculty() -> AllocationRunRead:
    entries = [
        _entry(),
        _entry(
            event_id="evt-2",
            slot_id="slot-2",
            day="tuesday",
            period_numbers=[2],
            faculty_ids=[20],
            faculty_names=["Dr B"],
        ),
    ]
    summaries = [
        FacultyWorkloadSummaryRead(
            faculty_id=10,
            full_name="Dr A",
            designation_key="assistant_professor",
            theory_weekly_hours=1,
            lab_weekly_hours=0,
            total_weekly_hours=1,
            theory_course_count=1,
            lab_course_count=0,
            lab_session_count=0,
        ),
        FacultyWorkloadSummaryRead(
            faculty_id=20,
            full_name="Dr B",
            designation_key="assistant_professor",
            theory_weekly_hours=1,
            lab_weekly_hours=0,
            total_weekly_hours=1,
            theory_course_count=1,
            lab_course_count=0,
            lab_session_count=0,
        ),
    ]
    plans = [
        BatchSemesterPlanRead(
            batch_code="2023-27",
            semester_number=5,
            section_count=1,
            working_days=["monday", "tuesday", "wednesday", "thursday", "friday"],
        )
    ]
    return AllocationRunRead(
        id=42,
        batch_plans=plans,
        batch_codes=["2023-27"],
        batch_code="2023-27",
        semester_number=5,
        section_count=1,
        status="feasible",
        timetable_status="feasible",
        objective_value=None,
        assignment_count=2,
        faculty_count=2,
        timetable_entry_count=2,
        faculty_summaries=summaries,
        timetable_entries=entries,
        timetable_grid=build_timetable_grid(entries),
        faculty_timetable_grids=build_faculty_timetable_grids(entries, summaries),
    )


def test_export_single_faculty_pdf_is_valid() -> None:
    run = _run_with_faculty()
    payload = export_single_faculty_pdf(run, faculty_id=10)
    assert payload.startswith(b"%PDF")
    assert single_faculty_pdf_filename(run, "Dr A") == "AIML_Timetable_Dr_A_run42.pdf"


def test_export_single_faculty_pdf_missing_raises() -> None:
    run = _run_with_faculty()
    with pytest.raises(TimetableExportError):
        export_single_faculty_pdf(run, faculty_id=999)


def _settings(**overrides: object) -> Settings:
    payload = {
        "fwp_smtp_host": "smtp.example.edu",
        "fwp_smtp_port": 587,
        "fwp_smtp_user": "bot",
        "fwp_smtp_password": "secret",
        "fwp_smtp_from": "timetable@example.edu",
        "fwp_smtp_use_tls": True,
        "fwp_app_name": "Faculty Workload Planning Agent",
    }
    payload.update(overrides)
    return Settings(**payload)


@pytest.mark.asyncio
async def test_mail_service_sends_one_message_per_faculty_with_email() -> None:
    run = _run_with_faculty()
    sent_messages: list[EmailMessage] = []

    def fake_sender(message: EmailMessage, _settings: Settings) -> None:
        sent_messages.append(message)

    members = {
        10: SimpleNamespace(id=10, full_name="Dr A", email="a@example.edu"),
        20: SimpleNamespace(id=20, full_name="Dr B", email="b@example.edu"),
    }
    session = AsyncMock()
    execute_result = MagicMock()
    execute_result.scalars.return_value.all.return_value = list(members.values())
    session.execute.return_value = execute_result

    service = TimetableMailService(settings=_settings(), smtp_sender=fake_sender)
    result = await service.send_faculty_timetables(session, run)

    assert result.sent == 2
    assert result.skipped == 0
    assert result.failed == 0
    assert len(sent_messages) == 2
    assert {msg["To"] for msg in sent_messages} == {"a@example.edu", "b@example.edu"}
    assert all(msg.get_content_maintype() == "multipart" for msg in sent_messages)


@pytest.mark.asyncio
async def test_mail_service_skips_missing_email_and_continues_after_failure() -> None:
    run = _run_with_faculty()
    # Add a third faculty grid with no email in DB.
    run.faculty_timetable_grids.append(
        FacultyTimetableGridRead(
            faculty_id=30,
            faculty_name="Dr C",
            grid=run.faculty_timetable_grids[0].grid,
        )
    )

    call_count = {"n": 0}

    def flaky_sender(message: EmailMessage, _settings: Settings) -> None:
        call_count["n"] += 1
        if message["To"] == "a@example.edu":
            raise smtplib_error()
        # success for others

    def smtplib_error() -> Exception:
        return RuntimeError("SMTP rejected recipient")

    members = {
        10: SimpleNamespace(id=10, full_name="Dr A", email="a@example.edu"),
        20: SimpleNamespace(id=20, full_name="Dr B", email="b@example.edu"),
        30: SimpleNamespace(id=30, full_name="Dr C", email=""),
    }
    session = AsyncMock()
    execute_result = MagicMock()
    execute_result.scalars.return_value.all.return_value = list(members.values())
    session.execute.return_value = execute_result

    service = TimetableMailService(settings=_settings(), smtp_sender=flaky_sender)
    result = await service.send_faculty_timetables(session, run)

    assert result.recipient_count == 3
    assert result.sent == 1
    assert result.skipped == 1
    assert result.failed == 1
    statuses = {row.faculty_id: row.status for row in result.details}
    assert statuses[10] == FacultyTimetableMailStatus.FAILED
    assert statuses[20] == FacultyTimetableMailStatus.SENT
    assert statuses[30] == FacultyTimetableMailStatus.SKIPPED


@pytest.mark.asyncio
async def test_mail_service_requires_smtp_config() -> None:
    run = _run_with_faculty()
    session = AsyncMock()
    service = TimetableMailService(
        settings=_settings(fwp_smtp_host="", fwp_smtp_from=""),
        smtp_sender=lambda *_args: None,
    )
    with pytest.raises(SmtpNotConfiguredError, match="SMTP is not configured"):
        await service.send_faculty_timetables(session, run)


def test_settings_smtp_configured_property() -> None:
    assert _settings().smtp_configured is True
    assert _settings(fwp_smtp_host="").smtp_configured is False
    assert _settings(fwp_smtp_from="  ").smtp_configured is False
