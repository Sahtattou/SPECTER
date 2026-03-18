from pydantic import BaseModel


class Settings(BaseModel):
    go_api_base_url: str = "http://localhost:8080"
