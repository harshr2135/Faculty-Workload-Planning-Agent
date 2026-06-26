"""Department ORM model."""

from __future__ import annotations

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.models.base import Base, TimestampMixin


class Department(Base, TimestampMixin):
    __tablename__ = "departments"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)

    faculty_members: Mapped[list["FacultyMember"]] = relationship(
        back_populates="department",
        cascade="all, delete-orphan",
    )
    academic_year_levels: Mapped[list["AcademicYearLevel"]] = relationship(
        back_populates="department",
        cascade="all, delete-orphan",
    )
    semesters: Mapped[list["Semester"]] = relationship(
        back_populates="department",
        cascade="all, delete-orphan",
    )
    classrooms: Mapped[list["Classroom"]] = relationship(
        back_populates="department",
        cascade="all, delete-orphan",
    )
    laboratories: Mapped[list["Laboratory"]] = relationship(
        back_populates="department",
        cascade="all, delete-orphan",
    )
    courses: Mapped[list["Course"]] = relationship(
        back_populates="department",
        cascade="all, delete-orphan",
    )
    student_batches: Mapped[list["StudentBatch"]] = relationship(
        back_populates="department",
        cascade="all, delete-orphan",
    )
    time_slots: Mapped[list["TimeSlot"]] = relationship(
        back_populates="department",
        cascade="all, delete-orphan",
        order_by="TimeSlot.sort_order",
    )
    designation_policies: Mapped[list["DesignationWorkloadPolicy"]] = relationship(
        back_populates="department",
        cascade="all, delete-orphan",
    )
    planning_policies: Mapped[list["PlanningPolicy"]] = relationship(
        back_populates="department",
        cascade="all, delete-orphan",
    )
