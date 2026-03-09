import logging
import traceback
from contextlib import asynccontextmanager

logging.basicConfig(level=logging.INFO)

from fastapi import FastAPI, Request
from fastapi.exceptions import HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import settings
from app.exceptions import NotFoundError, ValidationError, ConflictError
from app.services.batch_scheduler import cleanup_stale_running_records
from app.api.agent_versions import router as agent_versions_router
from app.api.batch_tests import router as batch_tests_router
from app.api.judge_configs import router as judge_configs_router
from app.api.model_configs import router as model_configs_router
from app.api.projects import router as projects_router
from app.api.providers import router as providers_router
from app.api.test_cases import router as test_cases_router

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    stale_batches, stale_results = await cleanup_stale_running_records()
    if stale_batches or stale_results:
        logger.warning(
            f"Startup cleanup: marked {stale_batches} stale batch(es) and "
            f"{stale_results} stale test result(s) as failed"
        )
    yield


app = FastAPI(title="对话 Agent 评测平台", version="0.1.0", redirect_slashes=False, lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(providers_router)
app.include_router(projects_router)
app.include_router(agent_versions_router)
app.include_router(test_cases_router)
app.include_router(judge_configs_router)
app.include_router(model_configs_router)
app.include_router(batch_tests_router)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    if isinstance(exc, HTTPException):
        raise exc
    logging.error(f"Unhandled exception: {exc}\n{traceback.format_exc()}")
    return JSONResponse(status_code=500, content={"detail": "服务器内部错误"})


@app.exception_handler(NotFoundError)
async def not_found_handler(request: Request, exc: NotFoundError):
    return JSONResponse(status_code=404, content={"detail": exc.message})


@app.exception_handler(ValidationError)
async def validation_error_handler(request: Request, exc: ValidationError):
    return JSONResponse(status_code=400, content={"detail": exc.message})


@app.exception_handler(ConflictError)
async def conflict_error_handler(request: Request, exc: ConflictError):
    return JSONResponse(status_code=409, content={"detail": exc.message})


@app.get("/api/health")
async def health_check():
    return {"status": "ok"}
