from __future__ import annotations

import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterator, List, Optional

from app.adversarial.models import IOCEnvelope


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class AdversarialStorage:
    def __init__(self, db_path: str) -> None:
        self.db_path = db_path
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    @contextmanager
    def _connect(self) -> Iterator[sqlite3.Connection]:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        finally:
            conn.close()

    def _init_db(self) -> None:
        with self._connect() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS mirror_events (
                    ioc_uuid TEXT PRIMARY KEY,
                    raw_value TEXT NOT NULL,
                    ioc_type TEXT NOT NULL,
                    source_name TEXT,
                    source_url TEXT,
                    source_query TEXT,
                    raw_evidence TEXT,
                    collected_at TEXT NOT NULL,
                    pipeline_stage TEXT NOT NULL,
                    is_synthetic INTEGER NOT NULL DEFAULT 0,
                    poison_attack_type TEXT,
                    poison_detected INTEGER,
                    detection_rule TEXT,
                    corroboration_count INTEGER NOT NULL DEFAULT 0,
                    domain_age_days INTEGER,
                    open_ports TEXT,
                    asn TEXT,
                    composite_score REAL,
                    score_breakdown TEXT,
                    days_to_attack_estimate TEXT,
                    threat_level TEXT,
                    analyst_notes TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS injections (
                    injection_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    injected_at TEXT NOT NULL,
                    attack_type TEXT NOT NULL,
                    raw_value TEXT NOT NULL,
                    detected INTEGER,
                    ioc_uuid TEXT,
                    detection_rule TEXT,
                    FOREIGN KEY(ioc_uuid) REFERENCES mirror_events(ioc_uuid)
                );

                CREATE TABLE IF NOT EXISTS pipeline_runs (
                    run_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    run_timestamp TEXT NOT NULL,
                    raw_value TEXT NOT NULL,
                    source_name TEXT,
                    ioc_uuid TEXT
                );

                CREATE INDEX IF NOT EXISTS idx_mirror_events_raw_value ON mirror_events(raw_value);
                CREATE INDEX IF NOT EXISTS idx_mirror_events_stage ON mirror_events(pipeline_stage);
                CREATE INDEX IF NOT EXISTS idx_injections_ioc_uuid ON injections(ioc_uuid);
                CREATE INDEX IF NOT EXISTS idx_pipeline_runs_raw_value_timestamp ON pipeline_runs(raw_value, run_timestamp);
                """
            )

    def save_event(self, envelope: IOCEnvelope) -> None:
        now = utc_now_iso()
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO mirror_events (
                    ioc_uuid, raw_value, ioc_type, source_name, source_url, source_query,
                    raw_evidence, collected_at, pipeline_stage, is_synthetic, poison_attack_type,
                    poison_detected, detection_rule, corroboration_count, domain_age_days,
                    open_ports, asn, composite_score, score_breakdown, days_to_attack_estimate,
                    threat_level, analyst_notes, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(ioc_uuid) DO UPDATE SET
                    raw_value=excluded.raw_value,
                    ioc_type=excluded.ioc_type,
                    source_name=excluded.source_name,
                    source_url=excluded.source_url,
                    source_query=excluded.source_query,
                    raw_evidence=excluded.raw_evidence,
                    collected_at=excluded.collected_at,
                    pipeline_stage=excluded.pipeline_stage,
                    is_synthetic=excluded.is_synthetic,
                    poison_attack_type=excluded.poison_attack_type,
                    poison_detected=excluded.poison_detected,
                    detection_rule=excluded.detection_rule,
                    corroboration_count=excluded.corroboration_count,
                    domain_age_days=excluded.domain_age_days,
                    open_ports=excluded.open_ports,
                    asn=excluded.asn,
                    composite_score=excluded.composite_score,
                    score_breakdown=excluded.score_breakdown,
                    days_to_attack_estimate=excluded.days_to_attack_estimate,
                    threat_level=excluded.threat_level,
                    analyst_notes=excluded.analyst_notes,
                    updated_at=excluded.updated_at
                """,
                (
                    envelope.ioc_uuid,
                    envelope.raw_value,
                    envelope.ioc_type,
                    envelope.source_name,
                    envelope.source_url,
                    envelope.source_query,
                    json.dumps(envelope.raw_evidence),
                    envelope.collected_at,
                    envelope.pipeline_stage,
                    1 if envelope.is_synthetic else 0,
                    envelope.poison_attack_type,
                    None
                    if envelope.poison_detected is None
                    else (1 if envelope.poison_detected else 0),
                    envelope.detection_rule,
                    envelope.corroboration_count,
                    envelope.domain_age_days,
                    json.dumps(envelope.open_ports),
                    envelope.asn,
                    envelope.composite_score,
                    json.dumps(envelope.score_breakdown),
                    envelope.days_to_attack_estimate,
                    envelope.threat_level,
                    envelope.analyst_notes,
                    now,
                    now,
                ),
            )

    def log_injection(
        self, *, attack_type: str, raw_value: str, ioc_uuid: Optional[str]
    ) -> None:
        with self._connect() as conn:
            conn.execute(
                "INSERT INTO injections (injected_at, attack_type, raw_value, detected, ioc_uuid, detection_rule) VALUES (?, ?, ?, ?, ?, ?)",
                (utc_now_iso(), attack_type, raw_value, None, ioc_uuid, None),
            )

    def update_injection_detection(
        self, *, ioc_uuid: str, detected: bool, detection_rule: Optional[str]
    ) -> None:
        with self._connect() as conn:
            conn.execute(
                "UPDATE injections SET detected = ?, detection_rule = ? WHERE ioc_uuid = ?",
                (1 if detected else 0, detection_rule, ioc_uuid),
            )

    def record_pipeline_run_values(self, envelopes: List[IOCEnvelope]) -> None:
        run_time = utc_now_iso()
        with self._connect() as conn:
            conn.executemany(
                "INSERT INTO pipeline_runs (run_timestamp, raw_value, source_name, ioc_uuid) VALUES (?, ?, ?, ?)",
                [
                    (run_time, env.raw_value, env.source_name, env.ioc_uuid)
                    for env in envelopes
                ],
            )

    def has_historical_raw_value_before_today(self, raw_value: str) -> bool:
        today = datetime.now(timezone.utc).date().isoformat()
        with self._connect() as conn:
            row = conn.execute(
                "SELECT 1 FROM pipeline_runs WHERE raw_value = ? AND date(run_timestamp) < date(?) LIMIT 1",
                (raw_value, today),
            ).fetchone()
            return row is not None

    def get_recent_events(self, limit: int = 200) -> List[Dict[str, Any]]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT * FROM mirror_events ORDER BY collected_at DESC LIMIT ?",
                (limit,),
            ).fetchall()
        return [self._row_to_event_dict(row) for row in rows]

    def get_injections(self, limit: int = 200) -> List[Dict[str, Any]]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT * FROM injections ORDER BY injection_id DESC LIMIT ?",
                (limit,),
            ).fetchall()
        return [dict(row) for row in rows]

    def get_metrics(self) -> Dict[str, Any]:
        with self._connect() as conn:
            total = conn.execute("SELECT COUNT(*) AS c FROM mirror_events").fetchone()[
                "c"
            ]
            validated = conn.execute(
                "SELECT COUNT(*) AS c FROM mirror_events WHERE pipeline_stage = 'validated'"
            ).fetchone()["c"]
            quarantined = conn.execute(
                "SELECT COUNT(*) AS c FROM mirror_events WHERE pipeline_stage = 'quarantined'"
            ).fetchone()["c"]
            injections = conn.execute(
                "SELECT COUNT(*) AS c FROM injections"
            ).fetchone()["c"]
            caught = conn.execute(
                "SELECT COUNT(*) AS c FROM injections WHERE detected = 1"
            ).fetchone()["c"]

        catch_rate = 0.0 if injections == 0 else round((caught / injections) * 100.0, 2)
        return {
            "total_events": total,
            "validated_events": validated,
            "quarantined_events": quarantined,
            "total_injections": injections,
            "caught_injections": caught,
            "catch_rate_percent": catch_rate,
        }

    @staticmethod
    def _row_to_event_dict(row: sqlite3.Row) -> Dict[str, Any]:
        payload = dict(row)
        payload["raw_evidence"] = json.loads(payload.get("raw_evidence") or "{}")
        payload["open_ports"] = json.loads(payload.get("open_ports") or "[]")
        payload["score_breakdown"] = json.loads(payload.get("score_breakdown") or "{}")
        payload["is_synthetic"] = bool(payload.get("is_synthetic"))
        poison_detected = payload.get("poison_detected")
        payload["poison_detected"] = (
            None if poison_detected is None else bool(poison_detected)
        )
        return payload
