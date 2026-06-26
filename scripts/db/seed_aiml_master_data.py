"""Seed AIML classrooms, laboratories, semesters, and year-level configuration."""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.database.session import get_session_factory, init_db  # noqa: E402
from backend.services.department_seed_service import DepartmentSeedService  # noqa: E402


async def run_seed() -> None:
    await init_db()
    session_factory = get_session_factory()
    async with session_factory() as session:
        service = DepartmentSeedService()
        result = await service.seed_aiml_resources(session)
        await session.commit()

    print("AIML department master data seeded.")
    for key, value in result.items():
        print(f"  {key}: {value}")


if __name__ == "__main__":
    asyncio.run(run_seed())
