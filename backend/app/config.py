from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "postgresql+asyncpg://eval_user:eval_pass@localhost:5432/eval_platform"
    debug: bool = False
    cors_origins: list[str] = ["http://localhost:5173"]
    allow_private_urls: bool = True
    file_storage_path: str = "/data/uploads"

    model_config = {"env_prefix": "EVAL_", "env_file": ".env"}


settings = Settings()
