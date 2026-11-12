from anyio.functools import lru_cache
from pydantic import SecretStr, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Products API"
    debug: bool = False
    secret_key: SecretStr = Field(min_length=64)
    access_token_expire_minutes: int = Field(default=30, gt=0)
    admin_password: SecretStr = Field(min_length=8)
    user_password: SecretStr = Field(min_length=8)
    database_url: str = "postgresql+psycopg://products:products@127.0.0.1:5432/products"

    mongodb_url: str | None = None
    mongodb_database: str = "products"

    redis_url: str | None = None
    attributes_cache_ttl_seconds: int = Field(default=30, gt=0)
    auth_rate_limit_per_minute: int = Field(default=5, gt=0)

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()


