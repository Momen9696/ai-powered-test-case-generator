"""FastAPI application factory."""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app import __version__
from app.config import get_settings
from app.database import create_session_factory
from app.models import Base
from app.routers.http import get_db, router
from app.schemas import AppError


def create_app() -> FastAPI:
    settings = get_settings()
    engine, factory = create_session_factory(settings)
    Base.metadata.create_all(engine)

    @asynccontextmanager
    async def lifespan(_app: FastAPI):
        Base.metadata.create_all(engine)
        yield

    app = FastAPI(
        title="AI-Powered Test Case Generator",
        version=__version__,
        summary="Turn requirements and user stories into reviewable test cases.",
        description=(
            "The default provider is a deterministic mock. It does not call an external model. "
            "OpenAI and Anthropic adapters are optional and read keys from the server environment."
        ),
        lifespan=lifespan,
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=False,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["Content-Type", "Authorization"],
    )

    def _get_db():
        db = factory()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = _get_db
    app.include_router(router)

    @app.exception_handler(AppError)
    async def handle_app_error(_request: Request, exc: AppError) -> JSONResponse:
        return JSONResponse(status_code=exc.status_code, content={"detail": exc.message})

    @app.get("/", include_in_schema=False)
    def root() -> dict:
        return {"name": "AI-Powered Test Case Generator", "docs": "/docs", "health": "/api/health"}

    return app


app = create_app()
