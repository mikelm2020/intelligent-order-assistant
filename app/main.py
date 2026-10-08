from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from openai import APIError
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from app.api.router import api_router
from app.core.config import settings
from app.core.database import SessionDep, engine
from app.exceptions.ai import AIConfigurationError


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    await engine.dispose()


app = FastAPI(
    lifespan=lifespan,
    title=settings.app_name,
    version="0.1.0",
)

app.include_router(api_router)


@app.get("/health", tags=["health"])
async def health_check() -> dict[str, str]:
    return {
        "status": "ok",
        "service": settings.app_name,
    }


@app.get("/ready", tags=["health"])
async def readiness(session: SessionDep) -> dict[str, str]:
    try:
        await session.execute(text("SELECT 1"))
        await session.execute(text("SELECT id FROM assistant_runs LIMIT 0"))
        await session.execute(text("SELECT thread_id FROM checkpoints LIMIT 0"))
        if not settings.operator_api_key or not settings.reviewer_api_key:
            raise HTTPException(503, "API credentials are not configured")
    except SQLAlchemyError as exc:
        raise HTTPException(503, "Database or schema is not ready") from exc
    return {"status": "ready"}


@app.exception_handler(APIError)
async def handle_ai_error(request: Request, exc: APIError):
    return JSONResponse(
        status_code=502, content={"detail": "AI provider temporarily unavailable"}
    )


@app.exception_handler(IntegrityError)
async def handle_integrity_error(request: Request, exc: IntegrityError):
    return JSONResponse(
        status_code=409, content={"detail": "Database constraint conflict"}
    )


@app.exception_handler(AIConfigurationError)
async def handle_ai_configuration_error(request: Request, exc: AIConfigurationError):
    return JSONResponse(
        status_code=503,
        content={"detail": "AI provider credentials are not configured"},
    )
