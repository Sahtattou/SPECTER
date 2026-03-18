from __future__ import annotations

from functools import lru_cache

from fastapi import FastAPI, HTTPException

from app.adversarial import AdversarialMirrorService
from app.chains.blue_analyst_chain import run_blue_analyst_chain
from app.chains.red_injector_chain import run_red_injector_chain
from app.clients.go_api_client import GoAPIClient
from app.config import get_settings
from app.schemas import (
    BlueAnalysisRequest,
    BlueAnalysisResponse,
    RedInjectionRequest,
    RedInjectionResponse,
    RunAgentRequest,
    RunAgentResponse,
)
from app.services.agent_runner import run_agent

app = FastAPI(title="SPECTER Agent Service", version="0.1.0")


@lru_cache(maxsize=1)
def get_adversarial_service() -> AdversarialMirrorService:
    settings = get_settings()
    service = AdversarialMirrorService(
        db_path=settings.adversarial_db_path,
        red_agent_interval_seconds=settings.red_agent_interval_seconds,
    )
    service.start()
    return service


@lru_cache(maxsize=1)
def get_client() -> GoAPIClient:
    settings = get_settings()
    return GoAPIClient(
        base_url=settings.go_api_base_url,
        timeout_seconds=settings.request_timeout_seconds,
        max_retries=settings.max_retries,
    )


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "specter-agents"}


@app.get("/ready")
def ready() -> dict[str, str]:
    try:
        get_client().health()
        get_adversarial_service().get_metrics()
    except Exception as exc:  # pragma: no cover - readiness is environment dependent
        raise HTTPException(
            status_code=503, detail=f"go-api-unavailable: {exc}"
        ) from exc
    return {"status": "ready"}


@app.post("/mirror/ingest")
def mirror_ingest(payload: dict) -> dict:
    return get_adversarial_service().ingest_real_ioc(payload)


@app.post("/mirror/injections/trigger")
def mirror_trigger_injection(payload: dict | None = None) -> dict:
    attack_type = None
    if isinstance(payload, dict):
        attack_type = payload.get("attack_type")
    try:
        return get_adversarial_service().trigger_injection(attack_type=attack_type)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/api/v1/agents/injections/trigger")
def api_v1_mirror_trigger_injection(payload: dict | None = None) -> dict:
    return mirror_trigger_injection(payload)


@app.get("/mirror/events")
def mirror_events(limit: int = 100, stage: str | None = None) -> dict:
    return {"events": get_adversarial_service().get_events(limit=limit, stage=stage)}


@app.get("/mirror/injections")
def mirror_injections(limit: int = 100) -> dict:
    return {"injections": get_adversarial_service().get_injection_activity(limit=limit)}


@app.get("/mirror/metrics")
def mirror_metrics() -> dict:
    return get_adversarial_service().get_metrics()


@app.post("/agents/blue/analyze", response_model=BlueAnalysisResponse)
def blue_analyze(request: BlueAnalysisRequest) -> BlueAnalysisResponse:
    return run_blue_analyst_chain(client=get_client(), limit=request.limit)


@app.post("/agents/red/inject", response_model=RedInjectionResponse)
def red_inject(request: RedInjectionRequest) -> RedInjectionResponse:
    return run_red_injector_chain(
        client=get_client(),
        attack_type=request.attack_type,
        dry_run=request.dry_run,
    )


@app.post("/agents/run", response_model=RunAgentResponse)
def run_any_agent(request: RunAgentRequest) -> RunAgentResponse:
    try:
        result = run_agent(
            name=request.agent_name,
            client=get_client(),
            limit=request.limit,
            dry_run=request.dry_run,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return RunAgentResponse(agent_name=request.agent_name, result=result)
