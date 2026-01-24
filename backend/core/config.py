from pydantic_settings import BaseSettings
from pydantic import Field
from functools import lru_cache


class Settings(BaseSettings):
    # Supabase
    supabase_url: str
    supabase_key: str
    supabase_service_role_key: str

    # JWT
    jwt_secret_key: str = Field(..., min_length=32)
    jwt_refresh_secret_key: str = ""  # Separate key for refresh tokens
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7

    # Application
    app_env: str = "production"
    debug: bool = False
    allowed_origins: str = "http://localhost:3000"

    # Rate limiting
    rate_limit_login: str = "5/minute"
    rate_limit_signup: str = "3/minute"
    rate_limit_password_reset: str = "3/minute"

    # Request limits
    max_request_body_size: int = 1_000_000  # 1MB

    class Config:
        env_file = ".env"
        case_sensitive = False

    @property
    def refresh_secret_key(self) -> str:
        """Use separate refresh key if set, otherwise derive from main key."""
        return self.jwt_refresh_secret_key or f"{self.jwt_secret_key}_refresh"


@lru_cache()
def get_settings() -> Settings:
    return Settings()
