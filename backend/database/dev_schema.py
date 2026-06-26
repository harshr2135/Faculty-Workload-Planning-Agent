"""Lightweight schema patches for development (until Alembic migrations)."""

from __future__ import annotations

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine

_PATCH_STATEMENTS: tuple[str, ...] = (
    """
    CREATE TABLE IF NOT EXISTS student_batches (
        id SERIAL PRIMARY KEY,
        department_id INTEGER NOT NULL REFERENCES departments(id) ON DELETE CASCADE,
        batch_code VARCHAR(20) NOT NULL,
        created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        CONSTRAINT uq_student_batches_dept_code UNIQUE (department_id, batch_code)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS lecture_halls (
        id SERIAL PRIMARY KEY,
        name VARCHAR(50) NOT NULL UNIQUE,
        min_combined_sections INTEGER NOT NULL DEFAULT 2,
        max_combined_sections INTEGER NOT NULL DEFAULT 3,
        capacity INTEGER NULL,
        created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
    )
    """,
    "ALTER TABLE courses ADD COLUMN IF NOT EXISTS batch_id INTEGER",
    "ALTER TABLE courses ADD COLUMN IF NOT EXISTS course_type VARCHAR(20)",
    """
    DO $$
    BEGIN
        IF NOT EXISTS (
            SELECT 1 FROM pg_constraint WHERE conname = 'fk_courses_batch_id'
        ) THEN
            ALTER TABLE courses
                ADD CONSTRAINT fk_courses_batch_id
                FOREIGN KEY (batch_id) REFERENCES student_batches(id) ON DELETE CASCADE;
        END IF;
    END $$
    """,
    """
    DO $$
    BEGIN
        IF EXISTS (
            SELECT 1 FROM pg_constraint WHERE conname = 'uq_courses_dept_code'
        ) THEN
            ALTER TABLE courses DROP CONSTRAINT uq_courses_dept_code;
        END IF;
    END $$
    """,
    """
    DO $$
    BEGIN
        IF NOT EXISTS (
            SELECT 1 FROM pg_constraint WHERE conname = 'uq_courses_dept_batch_code'
        ) THEN
            ALTER TABLE courses
                ADD CONSTRAINT uq_courses_dept_batch_code
                UNIQUE (department_id, batch_id, course_code);
        END IF;
    END $$
    """,
)


async def apply_dev_schema_patches(engine: AsyncEngine) -> None:
    async with engine.begin() as conn:
        for statement in _PATCH_STATEMENTS:
            await conn.execute(text(statement))
