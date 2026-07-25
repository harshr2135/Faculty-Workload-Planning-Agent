"""Email personal weekly timetable PDFs to faculty on an allocation run."""

from __future__ import annotations

import logging
import smtplib
from email.message import EmailMessage
from typing import Protocol

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.config.settings import Settings, get_settings
from backend.models import FacultyMember
from backend.schemas.allocation import AllocationRunRead
from backend.schemas.timetable_mail import (
    FacultyTimetableMailDetail,
    FacultyTimetableMailResult,
    FacultyTimetableMailStatus,
)
from backend.services.timetable_export_service import (
    TimetableExportError,
    export_single_faculty_pdf,
    single_faculty_pdf_filename,
)

logger = logging.getLogger(__name__)


class SmtpNotConfiguredError(ValueError):
    """Raised when SMTP host/from are missing."""


class SmtpSender(Protocol):
    def __call__(self, message: EmailMessage, settings: Settings) -> None: ...


def send_smtp_message(message: EmailMessage, settings: Settings) -> None:
    """Deliver one EmailMessage through the configured SMTP server."""
    with smtplib.SMTP(settings.fwp_smtp_host, settings.fwp_smtp_port, timeout=30) as client:
        if settings.fwp_smtp_use_tls:
            client.starttls()
        user = settings.fwp_smtp_user.strip()
        password = settings.fwp_smtp_password
        if user:
            client.login(user, password)
        client.send_message(message)


class TimetableMailService:
    def __init__(
        self,
        *,
        settings: Settings | None = None,
        smtp_sender: SmtpSender | None = None,
    ) -> None:
        self._settings = settings or get_settings()
        self._smtp_sender: SmtpSender = smtp_sender or send_smtp_message

    async def send_faculty_timetables(
        self,
        session: AsyncSession,
        run: AllocationRunRead,
    ) -> FacultyTimetableMailResult:
        if not self._settings.smtp_configured:
            raise SmtpNotConfiguredError(
                "SMTP is not configured. Set FWP_SMTP_HOST and FWP_SMTP_FROM in the environment."
            )

        grids = run.faculty_timetable_grids
        if not grids:
            return FacultyTimetableMailResult(
                run_id=run.id,
                recipient_count=0,
                sent=0,
                skipped=0,
                failed=0,
                details=[],
            )

        faculty_ids = [grid.faculty_id for grid in grids]
        result = await session.execute(
            select(FacultyMember).where(FacultyMember.id.in_(faculty_ids))
        )
        members = {member.id: member for member in result.scalars().all()}

        batch_label = ", ".join(run.batch_codes) if run.batch_codes else run.batch_code
        details: list[FacultyTimetableMailDetail] = []
        sent = skipped = failed = 0

        for grid in grids:
            member = members.get(grid.faculty_id)
            email = (member.email if member else "").strip()
            full_name = grid.faculty_name or (member.full_name if member else f"Faculty #{grid.faculty_id}")

            if not email:
                skipped += 1
                details.append(
                    FacultyTimetableMailDetail(
                        faculty_id=grid.faculty_id,
                        full_name=full_name,
                        email=None,
                        status=FacultyTimetableMailStatus.SKIPPED,
                        message="No email address on faculty roster.",
                    )
                )
                continue

            try:
                pdf_bytes = export_single_faculty_pdf(run, grid.faculty_id)
                attachment_name = single_faculty_pdf_filename(run, full_name)
                message = self._build_message(
                    run=run,
                    batch_label=batch_label,
                    full_name=full_name,
                    to_email=email,
                    pdf_bytes=pdf_bytes,
                    attachment_name=attachment_name,
                )
                self._smtp_sender(message, self._settings)
                sent += 1
                details.append(
                    FacultyTimetableMailDetail(
                        faculty_id=grid.faculty_id,
                        full_name=full_name,
                        email=email,
                        status=FacultyTimetableMailStatus.SENT,
                        message="Timetable PDF sent.",
                    )
                )
            except TimetableExportError as exc:
                failed += 1
                details.append(
                    FacultyTimetableMailDetail(
                        faculty_id=grid.faculty_id,
                        full_name=full_name,
                        email=email,
                        status=FacultyTimetableMailStatus.FAILED,
                        message=str(exc),
                    )
                )
                logger.warning(
                    "Faculty timetable export failed faculty_id=%s: %s",
                    grid.faculty_id,
                    exc,
                )
            except Exception as exc:  # noqa: BLE001 — continue batch on per-recipient failure
                failed += 1
                details.append(
                    FacultyTimetableMailDetail(
                        faculty_id=grid.faculty_id,
                        full_name=full_name,
                        email=email,
                        status=FacultyTimetableMailStatus.FAILED,
                        message=str(exc) or exc.__class__.__name__,
                    )
                )
                logger.warning(
                    "Faculty timetable email failed faculty_id=%s email=%s: %s",
                    grid.faculty_id,
                    email,
                    exc,
                )

        return FacultyTimetableMailResult(
            run_id=run.id,
            recipient_count=len(grids),
            sent=sent,
            skipped=skipped,
            failed=failed,
            details=details,
        )

    def _build_message(
        self,
        *,
        run: AllocationRunRead,
        batch_label: str,
        full_name: str,
        to_email: str,
        pdf_bytes: bytes,
        attachment_name: str,
    ) -> EmailMessage:
        message = EmailMessage()
        message["Subject"] = f"AIML weekly timetable — {batch_label} (run {run.id})"
        message["From"] = self._settings.fwp_smtp_from
        message["To"] = to_email
        message.set_content(
            (
                f"Dear {full_name},\n\n"
                f"Please find attached your weekly teaching timetable for AIML "
                f"({batch_label}, allocation run #{run.id}).\n\n"
                "This PDF shows only your scheduled sessions for the week.\n\n"
                "Regards,\n"
                f"{self._settings.fwp_app_name}\n"
            )
        )
        message.add_attachment(
            pdf_bytes,
            maintype="application",
            subtype="pdf",
            filename=attachment_name,
        )
        return message
