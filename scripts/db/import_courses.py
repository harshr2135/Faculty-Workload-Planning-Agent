"""Import course catalog from Excel into PostgreSQL."""

from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.database.session import get_session_factory, init_db  # noqa: E402
from backend.services.course_import_service import CourseImportService  # noqa: E402
from backend.services.department_seed_service import DepartmentSeedService  # noqa: E402


async def run_import(file_path: Path, seed_first: bool) -> None:
    if not file_path.exists():
        raise FileNotFoundError(f"Excel file not found: {file_path}")
    if file_path.suffix.lower() != ".xlsx":
        raise ValueError("Only .xlsx files are supported.")

    await init_db()
    session_factory = get_session_factory()

    async with session_factory() as session:
        if seed_first:
            seed_service = DepartmentSeedService()
            await seed_service.seed_aiml_resources(session)

        import_service = CourseImportService()
        result = await import_service.import_from_excel(session, source=file_path)
        await session.commit()

    print("Course import completed.")
    print(f"  Total rows processed: {result.total_rows}")
    print(f"  Created: {result.created}")
    print(f"  Updated: {result.updated}")
    if result.errors:
        print("  Warnings:")
        for error in result.errors:
            print(f"    - {error}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Import AIML courses from Excel.")
    parser.add_argument("file", type=Path, help="Path to Courses.xlsx")
    parser.add_argument(
        "--no-seed",
        action="store_true",
        help="Skip seeding classrooms/labs/semesters before import",
    )
    args = parser.parse_args()
    asyncio.run(run_import(args.file, seed_first=not args.no_seed))


if __name__ == "__main__":
    main()
