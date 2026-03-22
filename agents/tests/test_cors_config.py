import os

from app.config import Settings


def test_agent_allowed_origins_defaults() -> None:
    os.environ.pop("AGENT_ALLOWED_ORIGINS", None)
    settings = Settings.from_env()
    assert "http://localhost:1420" in settings.agent_allowed_origins
    assert "tauri://localhost" in settings.agent_allowed_origins
