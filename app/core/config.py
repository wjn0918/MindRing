from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime settings loaded from environment variables or a local .env file."""

    app_name: str = "微光年轮 API"
    environment: str = "development"
    database_url: str = Field(
        default="mysql+pymysql://mindring:mindring@127.0.0.1:3306/mindring?charset=utf8mb4",
        description="SQLAlchemy database URL. Use a MySQL URL in production.",
    )
    wechat_app_id: str | None = None
    wechat_app_secret: str | None = None
    enable_content_safety: bool = False

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


@lru_cache
def get_settings() -> Settings:
    return Settings()
