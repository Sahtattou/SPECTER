from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field


class EventRecord(BaseModel):
    ioc_value: str = Field(default="")
    ioc_type: str = Field(default="unknown")
    threat_level: str = Field(default="UNKNOWN")
    composite_score: float = Field(default=0.0)
    source_name: str = Field(default="unknown")


class BlueAnalysisRequest(BaseModel):
    limit: int = Field(default=100, ge=1, le=500)


class BlueAnalysisResponse(BaseModel):
    summary: str
    total_events: int
    by_threat_level: Dict[str, int]
    top_iocs: List[str]
    recommended_actions: List[str]


class RedInjectionRequest(BaseModel):
    attack_type: Optional[str] = None
    dry_run: bool = True


class RedInjectionResponse(BaseModel):
    attack_type: str
    payload: Dict[str, Any]
    submitted: bool
    target_endpoint: str
    notes: str


class RunAgentRequest(BaseModel):
    agent_name: Literal["blue_analyst", "red_injector"]
    limit: int = Field(default=100, ge=1, le=500)
    dry_run: bool = True


class RunAgentResponse(BaseModel):
    agent_name: str
    result: Dict[str, Any]
