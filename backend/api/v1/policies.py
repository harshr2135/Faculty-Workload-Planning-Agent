"""Workload policy API routes."""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database.session import get_db_session
from backend.schemas.policy import PolicyOverviewRead
from backend.services.policy_service import PolicySeedService, PolicyService

router = APIRouter(prefix="/policies", tags=["policies"])


@router.get("", response_model=PolicyOverviewRead)
async def list_policies(
    session: AsyncSession = Depends(get_db_session),
) -> PolicyOverviewRead:
    service = PolicyService()
    return await service.get_overview(session)


@router.post("/seed-aiml")
async def seed_aiml_policies(
    session: AsyncSession = Depends(get_db_session),
) -> dict[str, int]:
    service = PolicySeedService()
    return await service.seed_aiml_policies(session)
