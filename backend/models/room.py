"""Classroom and laboratory ORM models."""

from __future__ import annotations

from sqlalchemy import ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.models.base import Base, TimestampMixin


class Classroom(Base, TimestampMixin):
    __tablename__ = "classrooms"
    __table_args__ = (
        UniqueConstraint(
            "department_id",
            "room_number",
            name="uq_classrooms_dept_room",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    department_id: Mapped[int] = mapped_column(
        ForeignKey("departments.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    room_number: Mapped[str] = mapped_column(String(20), nullable=False)
    capacity: Mapped[int | None] = mapped_column(Integer, nullable=True)

    department: Mapped["Department"] = relationship(back_populates="classrooms")


class Laboratory(Base, TimestampMixin):
    __tablename__ = "laboratories"
    __table_args__ = (
        UniqueConstraint(
            "department_id",
            "room_number",
            name="uq_laboratories_dept_room",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    department_id: Mapped[int] = mapped_column(
        ForeignKey("departments.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    room_number: Mapped[str] = mapped_column(String(20), nullable=False)
    capacity: Mapped[int | None] = mapped_column(Integer, nullable=True)

    department: Mapped["Department"] = relationship(back_populates="laboratories")


class LectureHall(Base, TimestampMixin):
    """College-wide hall for combined-section PEC/SEC delivery."""

    __tablename__ = "lecture_halls"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    min_combined_sections: Mapped[int] = mapped_column(Integer, nullable=False, default=2)
    max_combined_sections: Mapped[int] = mapped_column(Integer, nullable=False, default=3)
    capacity: Mapped[int | None] = mapped_column(Integer, nullable=True)
