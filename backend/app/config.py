from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "postgresql+asyncpg://luohuibin@localhost:5432/eval_platform"
    debug: bool = False
    cors_origins: list[str] = ["http://localhost:5173"]

    model_config = {"env_prefix": "EVAL_", "env_file": ".env"}


settings = Settings()
