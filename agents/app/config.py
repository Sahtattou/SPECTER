import os
from functools import lru_cache

from pydantic import BaseModel, Field


class Settings(BaseModel):
    go_api_base_url: str = Field(default="http://localhost:8080")
    request_timeout_seconds: int = Field(default=10)
    max_retries: int = Field(default=2)
    agent_model: str = Field(default="gpt-4.1-mini")

    @classmethod
    def from_env(cls) -> "Settings":
        return cls(
            go_api_base_url=os.getenv("GO_API_BASE_URL", "http://localhost:8080"),
            request_timeout_seconds=int(os.getenv("AGENT_REQUEST_TIMEOUT_SECONDS", "10")),
            max_retries=int(os.getenv("AGENT_MAX_RETRIES", "2")),
            agent_model=os.getenv("AGENT_MODEL", "gpt-4.1-mini"),
        )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings.from_env()
