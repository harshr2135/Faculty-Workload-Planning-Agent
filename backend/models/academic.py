"""Academic year levels and semester ORM models."""

from __future__ import annotations

from sqlalchemy import ForeignKey, Integer, JSON, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.models.base import Base, TimestampMixin


class StudentBatch(Base, TimestampMixin):
    """Admission cohort (e.g. 2023-27) for a department."""

    __tablename__ = "student_batches"
    __table_args__ = (
        UniqueConstraint(
            "department_id",
            "batch_code",
            name="uq_student_batches_dept_code",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    department_id: Mapped[int] = mapped_column(
        ForeignKey("departments.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    batch_code: Mapped[str] = mapped_column(String(20), nullable=False)

    department: Mapped["Department"] = relationship(back_populates="student_batches")
    courses: Mapped[list["Course"]] = relationship(
        back_populates="batch",
        cascade="all, delete-orphan",
    )


class AcademicYearLevel(Base, TimestampMixin):
    """Student year band within a department (e.g. 2nd year = sem 3–4)."""

    __tablename__ = "academic_year_levels"
    __table_args__ = (
        UniqueConstraint(
            "department_id",
            "year_level",
            name="uq_academic_year_levels_dept_year",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    department_id: Mapped[int] = mapped_column(
        ForeignKey("departments.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    year_level: Mapped[int] = mapped_column(Integer, nullable=False)
    label: Mapped[str] = mapped_column(String(50), nullable=False)
    section_count: Mapped[int] = mapped_column(Integer, nullable=False)
    working_days: Mapped[list[str]] = mapped_column(JSON, nullable=False)

    department: Mapped["Department"] = relationship(back_populates="academic_year_levels")
    semesters: Mapped[list["Semester"]] = relationship(
        back_populates="academic_year_level",
        cascade="all, delete-orphan",
    )


class Semester(Base, TimestampMixin):
    __tablename__ = "semesters"
    __table_args__ = (
        UniqueConstraint(
            "department_id",
            "semester_number",
            name="uq_semesters_dept_number",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    department_id: Mapped[int] = mapped_column(
        ForeignKey("departments.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    academic_year_level_id: Mapped[int] = mapped_column(
        ForeignKey("academic_year_levels.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    semester_number: Mapped[int] = mapped_column(Integer, nullable=False)

    department: Mapped["Department"] = relationship(back_populates="semesters")
    academic_year_level: Mapped[AcademicYearLevel] = relationship(back_populates="semesters")
    courses: Mapped[list["Course"]] = relationship(
        back_populates="semester",
        cascade="all, delete-orphan",
    )
