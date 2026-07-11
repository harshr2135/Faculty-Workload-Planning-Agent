"""Course ORM model."""

from __future__ import annotations

from sqlalchemy import ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.core.domain.course_type_config import supports_lab_practicals, uses_lecture_hall
from backend.models.base import Base, TimestampMixin


class Course(Base, TimestampMixin):
    __tablename__ = "courses"
    __table_args__ = (
        UniqueConstraint(
            "department_id",
            "batch_id",
            "semester_id",
            "course_code",
            name="uq_courses_dept_batch_semester_code",
        ),
    )

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
    course_type: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(300), nullable=False)
    course_code: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    credits: Mapped[int] = mapped_column(Integer, nullable=False)
    lectures_per_week: Mapped[int] = mapped_column(Integer, nullable=False)
    practical_hours: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        doc="Continuous lab block duration in hours; 0 means no lab.",
    )

    department: Mapped["Department"] = relationship(back_populates="courses")
    batch: Mapped["StudentBatch"] = relationship(back_populates="courses")
    semester: Mapped["Semester"] = relationship(back_populates="courses")

    @property
    def has_lab(self) -> bool:
        return supports_lab_practicals(self.course_type, self.practical_hours)

    @property
    def requires_lecture_hall(self) -> bool:
        return uses_lecture_hall(self.course_type)
