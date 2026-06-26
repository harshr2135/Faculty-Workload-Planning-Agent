"""API v1 router aggregation."""

from fastapi import APIRouter

from backend.api.v1.courses import router as courses_router
from backend.api.v1.faculty import router as faculty_router
from backend.api.v1.policies import router as policies_router
from backend.api.v1.timetable import router as timetable_router

api_router = APIRouter()
api_router.include_router(faculty_router)
api_router.include_router(courses_router)
api_router.include_router(timetable_router)
api_router.include_router(policies_router)
