from functools import lru_cache
from urllib.parse import quote_plus

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime settings loaded from environment variables or a local .env file."""

    app_name: str = "微光年轮 API"
    environment: str = "development"
    database_url: str | None = Field(
        default=None,
        description="Full SQLAlchemy database URL. Takes precedence over MYSQL_* settings.",
    )
    mysql_host: str = "127.0.0.1"
    mysql_port: int = 3306
    mysql_user: str = "mindring"
    mysql_password: str = "mindring"
    mysql_database: str = "mindring"
    mysql_charset: str = "utf8mb4"
    wechat_app_id: str | None = None
    wechat_app_secret: str | None = None
    enable_content_safety: bool = False
    jwt_secret_key: str = "mindring-secret-key"
    jwt_algorithm: str = "HS256"
    jwt_expire_hours: int = 24 * 30

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    @property
    def sqlalchemy_database_url(self) -> str:
        if self.database_url:
            return self.database_url
        password = quote_plus(self.mysql_password)
        return (
            f"mysql+pymysql://{self.mysql_user}:{password}@"
            f"{self.mysql_host}:{self.mysql_port}/{self.mysql_database}?charset={self.mysql_charset}"
        )


@lru_cache
def get_settings() -> Settings:
    return Settings()
