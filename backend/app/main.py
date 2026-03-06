from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.api.agent_versions import router as agent_versions_router
from app.api.batch_tests import router as batch_tests_router
from app.api.judge_configs import router as judge_configs_router
from app.api.model_configs import router as model_configs_router
from app.api.projects import router as projects_router
from app.api.providers import router as providers_router
from app.api.test_cases import router as test_cases_router

app = FastAPI(title="对话 Agent 评测平台", version="0.1.0")

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


@app.get("/api/health")
async def health_check():
    return {"status": "ok"}
