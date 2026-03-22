import os
from functools import lru_cache

from pydantic import BaseModel, Field


class Settings(BaseModel):
    go_api_base_url: str = Field(default="http://localhost:8080")
    agent_allowed_origins: list[str] = Field(
        default_factory=lambda: [
            "http://localhost:5173",
            "http://127.0.0.1:5173",
            "http://localhost:1420",
            "http://127.0.0.1:1420",
            "tauri://localhost",
        ]
    )
    request_timeout_seconds: int = Field(default=10)
    max_retries: int = Field(default=2)
    agent_model: str = Field(default="gpt-4.1-mini")
    red_agent_interval_seconds: int = Field(default=30)
    adversarial_db_path: str = Field(default="./specter_adversarial.db")
    red_max_ratio: float = Field(default=1.0)
    min_real_events_before_auto_red: int = Field(default=5)
    go_sync_interval_seconds: int = Field(default=15)
    go_sync_batch_limit: int = Field(default=20)
    go_sync_on_startup: bool = Field(default=False)

    @classmethod
    def from_env(cls) -> "Settings":
        allowed_origins = [
            origin.strip()
            for origin in os.getenv(
                "AGENT_ALLOWED_ORIGINS",
                "http://localhost:5173,http://127.0.0.1:5173,http://localhost:1420,http://127.0.0.1:1420,tauri://localhost",
            ).split(",")
            if origin.strip()
        ]
        return cls(
            go_api_base_url=os.getenv("GO_API_BASE_URL", "http://localhost:8080"),
            agent_allowed_origins=allowed_origins,
            request_timeout_seconds=int(
                os.getenv("AGENT_REQUEST_TIMEOUT_SECONDS", "10")
            ),
            max_retries=int(os.getenv("AGENT_MAX_RETRIES", "2")),
            agent_model=os.getenv("AGENT_MODEL", "gpt-4.1-mini"),
            red_agent_interval_seconds=int(
                os.getenv("RED_AGENT_INTERVAL_SECONDS", "30")
            ),
            adversarial_db_path=os.getenv(
                "ADVERSARIAL_DB_PATH", "./specter_adversarial.db"
            ),
            red_max_ratio=float(os.getenv("RED_MAX_RATIO", "1.0")),
            min_real_events_before_auto_red=int(
                os.getenv("MIN_REAL_EVENTS_BEFORE_AUTO_RED", "5")
            ),
            go_sync_interval_seconds=int(os.getenv("GO_SYNC_INTERVAL_SECONDS", "15")),
            go_sync_batch_limit=int(os.getenv("GO_SYNC_BATCH_LIMIT", "20")),
            go_sync_on_startup=os.getenv("GO_SYNC_ON_STARTUP", "false").lower()
            in {"1", "true", "yes", "on"},
        )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings.from_env()
