"""Allocation run persistence."""

from __future__ import annotations

from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.models.base import Base, TimestampMixin


class AllocationRun(Base, TimestampMixin):
    __tablename__ = "allocation_runs"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    department_id: Mapped[int] = mapped_column(
        ForeignKey("departments.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    batch_id: Mapped[int] = mapped_column(
        ForeignKey("student_batches.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    semester_id: Mapped[int] = mapped_column(
        ForeignKey("semesters.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    status: Mapped[str] = mapped_column(String(30), nullable=False)
    objective_value: Mapped[int | None] = mapped_column(Integer, nullable=True)
    solution: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    department: Mapped["Department"] = relationship()
    batch: Mapped["StudentBatch"] = relationship()
    semester: Mapped["Semester"] = relationship()
