"""Import faculty members from an Excel file into PostgreSQL."""

from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path

# Allow running from project root without installing editable package paths.
PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.database.session import get_session_factory, init_db  # noqa: E402
from backend.services.faculty_import_service import FacultyImportService  # noqa: E402


async def run_import(file_path: Path) -> None:
    if not file_path.exists():
        raise FileNotFoundError(f"Excel file not found: {file_path}")
    if file_path.suffix.lower() != ".xlsx":
        raise ValueError("Only .xlsx files are supported.")

    await init_db()

    session_factory = get_session_factory()
    async with session_factory() as session:
        service = FacultyImportService()
        result = await service.import_from_excel(session, source=file_path)
        await session.commit()

    print("Import completed.")
    print(f"  Total rows processed: {result.total_rows}")
    print(f"  Created: {result.created}")
    print(f"  Updated: {result.updated}")
    print(f"  Departments: {', '.join(result.departments)}")
    if result.errors:
        print("  Row warnings:")
        for error in result.errors:
            print(f"    - {error}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Import faculty Excel data into PostgreSQL.")
    parser.add_argument(
        "file",
        type=Path,
        help="Path to the .xlsx file (e.g. AIML_Faculties_Details.xlsx)",
    )
    args = parser.parse_args()
    asyncio.run(run_import(args.file))


if __name__ == "__main__":
    main()
