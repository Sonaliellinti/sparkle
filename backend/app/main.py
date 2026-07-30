"""
FastAPI application entrypoint.

Run locally with:
    uvicorn app.main:app --reload

Swagger docs: http://localhost:8000/docs
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import api_router
from app.core.config import settings
from app.core.database import Base, engine

# Import models so their tables are registered on Base.metadata before
# create_all runs. (Also imported via app.models, kept explicit here for
# clarity on startup.)
import app.models  # noqa: F401


def create_tables() -> None:
    """Dev-time convenience: create any tables that don't exist yet.
    In production, prefer Alembic migrations (`alembic upgrade head`)
    instead of relying on this."""
    Base.metadata.create_all(bind=engine)


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.APP_NAME,
        description=(
            "Sparkle -- AI-powered interview readiness platform. Diagnose "
            "skills. Practice smarter. Get interview ready. Deterministic "
            "diagnosis engine across DSA, Python, SQL, and ML; LLM used only "
            "for explanations, roadmaps, and tutoring."
        ),
        version="0.1.0",
        docs_url="/docs",
        redoc_url="/redoc",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(api_router, prefix=settings.API_V1_PREFIX)

    @app.get("/", tags=["health"])
    def root():
        return {"app": settings.APP_NAME, "status": "ok", "environment": settings.ENVIRONMENT}

    @app.get("/health", tags=["health"])
    def health():
        return {"status": "healthy"}

    return app


app = create_app()

# Dev convenience: auto-create tables on import so `uvicorn app.main:app`
# works immediately with zero setup. In production, Alembic migrations
# (`alembic upgrade head`, run as the Docker CMD's first step) are the
# source of truth for schema changes — we deliberately do NOT call
# create_all() there, so a forgotten migration fails loudly instead of
# silently patching over it.
if settings.ENVIRONMENT != "production":
    create_tables()
