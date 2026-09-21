from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List
import json


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
    )

    environment: str = Field(default="development")
    debug: bool = Field(default=True)
    log_level: str = Field(default="INFO")

    # Database
    database_url: str = Field(default="sqlite+aiosqlite:///./storage/seedance.db")

    # JWT
    jwt_secret_key: str = Field(default="seedance-dev-jwt-secret-key")
    jwt_algorithm: str = Field(default="HS256")
    jwt_expire_minutes: int = Field(default=1440)

    # CORS
    cors_origins_str: str = Field(default='["http://localhost:3000"]', alias="CORS_ORIGINS")

    @property
    def cors_origins(self) -> List[str]:
        return json.loads(self.cors_origins_str)

    # File Storage
    storage_path: str = Field(default="./storage")
    upload_path: str = Field(default="./storage/uploads")
    video_path: str = Field(default="./storage/videos")
    image_path: str = Field(default="./storage/images")
    temp_path: str = Field(default="./storage/temp")

    # Email SMTP
    smtp_host: str = Field(default="154.12.30.33")
    smtp_port: int = Field(default=587)
    smtp_user: str = Field(default="postmaster@sxls.fun")
    smtp_pass: str = Field(default="MailServer2026!Secure")

    # Default API Configuration
    default_llm_api_type: str = Field(default="ark")
    default_llm_base_url: str = Field(default="https://ark.cn-beijing.volces.com/api/v3")
    default_llm_api_key: str = Field(default="ark-90187850-f8a6-47d1-9242-8a3e1fb62f96-97873")
    default_llm_model_main: str = Field(default="doubao-seed-2-0-mini-260428")
    default_llm_model_fast: str = Field(default="doubao-seed-2-0-lite-260428")

    default_seedream_api_type: str = Field(default="ark")
    default_seedream_base_url: str = Field(default="https://ark.cn-beijing.volces.com/api/v3/images/generations")
    default_seedream_api_key: str = Field(default="ark-90187850-f8a6-47d1-9242-8a3e1fb62f96-97873")
    default_seedream_model: str = Field(default="doubao-seedream-5-0-260128")

    default_seedance_api_type: str = Field(default="ark")
    default_seedance_base_url: str = Field(default="https://ark.cn-beijing.volces.com/api/v3/contents/generations/tasks")
    default_seedance_api_key: str = Field(default="ark-90187850-f8a6-47d1-9242-8a3e1fb62f96-97873")
    default_seedance_model: str = Field(default="doubao-seedance-2-0-260128")


settings = Settings()
