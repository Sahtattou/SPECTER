from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import uuid4


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class IOCEnvelope:
    ioc_uuid: str = field(default_factory=lambda: str(uuid4()))
    raw_value: str = ""
    ioc_type: str = "unknown"

    source_name: str = "unknown"
    source_url: Optional[str] = None
    source_query: Optional[str] = None
    raw_evidence: Dict[str, Any] = field(default_factory=dict)
    collected_at: str = field(default_factory=utc_now_iso)

    pipeline_stage: str = "raw_ingest"

    is_synthetic: bool = False
    poison_attack_type: Optional[str] = None
    poison_detected: Optional[bool] = None
    detection_rule: Optional[str] = None

    corroboration_count: int = 0
    domain_age_days: Optional[int] = None
    open_ports: List[int] = field(default_factory=list)
    asn: Optional[str] = None

    composite_score: Optional[float] = None
    score_breakdown: Dict[str, Any] = field(default_factory=dict)
    days_to_attack_estimate: Optional[str] = None
    threat_level: Optional[str] = None
    analyst_notes: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, payload: Dict[str, Any]) -> "IOCEnvelope":
        return cls(
            ioc_uuid=str(payload.get("ioc_uuid") or str(uuid4())),
            raw_value=str(payload.get("raw_value") or payload.get("ioc_value") or ""),
            ioc_type=str(payload.get("ioc_type") or "unknown"),
            source_name=str(payload.get("source_name") or "unknown"),
            source_url=payload.get("source_url"),
            source_query=payload.get("source_query"),
            raw_evidence=payload.get("raw_evidence") or {},
            collected_at=str(payload.get("collected_at") or utc_now_iso()),
            pipeline_stage=str(payload.get("pipeline_stage") or "raw_ingest"),
            is_synthetic=bool(payload.get("is_synthetic", False)),
            poison_attack_type=payload.get("poison_attack_type"),
            poison_detected=payload.get("poison_detected"),
            detection_rule=payload.get("detection_rule"),
            corroboration_count=int(payload.get("corroboration_count") or 0),
            domain_age_days=payload.get("domain_age_days"),
            open_ports=[int(port) for port in (payload.get("open_ports") or [])],
            asn=payload.get("asn"),
            composite_score=payload.get("composite_score"),
            score_breakdown=payload.get("score_breakdown") or {},
            days_to_attack_estimate=payload.get("days_to_attack_estimate"),
            threat_level=payload.get("threat_level"),
            analyst_notes=payload.get("analyst_notes"),
        )
