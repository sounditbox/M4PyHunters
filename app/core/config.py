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
    database_url: str = "sqlite+pysqlite:///./products.db"

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()


