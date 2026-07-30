"""Aggregates every route module under a single `/api/v1` prefix."""
from fastapi import APIRouter

from app.api.routes import ai, auth, concepts, dashboard, diagnosis, quiz

api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(concepts.router)
api_router.include_router(quiz.router)
api_router.include_router(diagnosis.router)
api_router.include_router(dashboard.router)
api_router.include_router(ai.router)
