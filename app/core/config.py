from functools import lru_cache
from typing import Literal

from pydantic import Field, SecretStr, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Intelligent Order Assistant"
    environment: str = "development"

    database_url: str = Field(repr=False)

    operator_api_key: SecretStr | None = None
    reviewer_api_key: SecretStr | None = None
    approval_ttl_seconds: int = 900

    @model_validator(mode="after")
    def distinct_credentials(self):
        if self.operator_api_key and self.reviewer_api_key:
            if (
                self.operator_api_key.get_secret_value()
                == self.reviewer_api_key.get_secret_value()
            ):
                raise ValueError("Operator and reviewer credentials must be distinct")
            if (
                min(
                    len(self.operator_api_key.get_secret_value()),
                    len(self.reviewer_api_key.get_secret_value()),
                )
                < 32
            ):
                raise ValueError("API credentials must have at least 32 characters")
        if self.approval_ttl_seconds <= 0:
            raise ValueError("Approval TTL must be positive")
        return self

    ai_provider: Literal["openai", "demo"] = "openai"
    openai_api_key: SecretStr | None = None
    openai_embedding_model: str = "text-embedding-3-small"
    openai_chat_model: str = "gpt-5.6-luna"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        hide_input_in_errors=True,
    )

    rag_max_distance: float = Field(default=0.4, ge=0, le=2)


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
