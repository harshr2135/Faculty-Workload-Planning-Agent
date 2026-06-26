"""Timetable time slot ORM model."""

from __future__ import annotations

from datetime import time

from sqlalchemy import ForeignKey, Integer, String, Time, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.models.base import Base, TimestampMixin


class TimeSlot(Base, TimestampMixin):
    """Daily period template (reused on each working day of the week)."""

    __tablename__ = "time_slots"
    __table_args__ = (
        UniqueConstraint(
            "department_id",
            "sort_order",
            name="uq_time_slots_dept_sort_order",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    department_id: Mapped[int] = mapped_column(
        ForeignKey("departments.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False)
    period_number: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        doc="Teaching period 1–7; null for break or lunch.",
    )
    label: Mapped[str] = mapped_column(String(50), nullable=False)
    start_time: Mapped[time] = mapped_column(Time, nullable=False)
    end_time: Mapped[time] = mapped_column(Time, nullable=False)
    slot_type: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        doc="teaching | break | lunch",
    )

    department: Mapped["Department"] = relationship(back_populates="time_slots")

    @property
    def duration_minutes(self) -> int:
        start_minutes = self.start_time.hour * 60 + self.start_time.minute
        end_minutes = self.end_time.hour * 60 + self.end_time.minute
        return end_minutes - start_minutes

    @property
    def is_teaching_slot(self) -> bool:
        return self.slot_type == "teaching"
