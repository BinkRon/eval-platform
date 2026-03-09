from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "postgresql+asyncpg://bink@localhost:5432/eval_platform"
    debug: bool = False
    cors_origins: list[str] = ["http://localhost:5173"]
    allow_private_urls: bool = False

    model_config = {"env_prefix": "EVAL_", "env_file": ".env"}


settings = Settings()
