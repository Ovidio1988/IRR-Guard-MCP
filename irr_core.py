from __future__ import annotations

import hashlib
import json
import sqlite3
import threading
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

LEVEL_ORDER = {"minimum": 0, "basic": 1, "extended": 2, "reinforced": 3}
LEVEL_LABELS = {
    "minimum": "Mínimo",
    "basic": "Básico",
    "extended": "Extendido",
    "reinforced": "Reforzado",
}

USAGE_BASELINE = {
    "search": "minimum",
    "summary": "basic",
    "partial_draft": "extended",
    "full_draft": "reinforced",
    "other": "basic",
}

MATERIALITY_FIELDS = [
    "ratio_decidendi",
    "facts_or_evidence",
    "subsumption_or_ruling",
    "fundamental_rights",
    "new_sources_or_arguments",
    "omission_risk",
    "alerts_or_external_imports",
    "challenged_by_party",
]

CRITICAL_FIELDS = {
    "facts_or_evidence",
    "subsumption_or_ruling",
    "fundamental_rights",
}

SENSITIVE_DOMAINS = {
    "criminal",
    "sanctioning",
    "family_minors",
    "detention",
    "asylum_immigration",
    "discrimination",
}

SOURCE_CHECKS = [
    "identifier_syntax",
    "existence",
    "document_match",
    "proposition_fidelity",
    "temporal_validity",
    "ratio_obiter",
    "contrary_authority",
    "record_fidelity",
]

ALERT_TYPES = {
    "hallucination",
    "contradiction",
    "omission",
    "personal_data",
    "bias",
    "prompt_injection",
    "external_import",
    "model_change",
    "source_manipulation",
    "verifier_error",
    "other",
}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def max_level(*levels: str) -> str:
    return max(levels, key=lambda x: LEVEL_ORDER[x])


def assess_materiality(usage_type: str, domain: str, factors: Dict[str, bool]) -> Dict[str, Any]:
    """Translate the article's material-incidence test into a conservative demo rule engine.

    The article does not prescribe a numeric score. This function therefore exposes the
    rule path instead of pretending there is a validated risk score.
    """
    baseline = USAGE_BASELINE.get(usage_type, "basic")
    level = baseline
    reasons: List[str] = [f"Nivel base por tipo de asistencia: {LEVEL_LABELS[baseline]}"]

    active = [field for field in MATERIALITY_FIELDS if bool(factors.get(field))]
    if active:
        level = max_level(level, "extended")
        reasons.append("Se activa trazabilidad extendida por incidencia material: " + ", ".join(active))

    critical_active = sorted(CRITICAL_FIELDS.intersection(active))
    if critical_active:
        level = "reinforced"
        reasons.append("Nivel reforzado por incidencia directa en hechos/prueba, subsunción/fallo o derechos fundamentales")

    if domain in SENSITIVE_DOMAINS and active:
        level = "reinforced"
        reasons.append("Umbral reforzado aplicado con especial prudencia por materia sensible")

    if usage_type == "full_draft":
        level = "reinforced"
        reasons.append("Borrador íntegro: matriz de proporcionalidad del IRR → reforzado")

    return {
        "level": level,
        "level_label": LEVEL_LABELS[level],
        "baseline": baseline,
        "active_factors": active,
        "reasons": reasons,
        "rule_note": "Regla conservadora de demostración; requiere validación empírica antes de uso institucional.",
    }


def required_source_checks(level: str) -> List[str]:
    if level == "minimum":
        return []
    if level == "basic":
        return ["existence", "document_match", "record_fidelity"]
    return [
        "existence",
        "document_match",
        "proposition_fidelity",
        "temporal_validity",
        "ratio_obiter",
        "contrary_authority",
        "record_fidelity",
    ]


@dataclass
class CloseResult:
    closed: bool
    blockers: List[str]
    report: Dict[str, Any]


class IRRStore:
    def __init__(self, db_path: str | Path):
        self.db_path = str(db_path)
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.RLock()
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path, timeout=10, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS cases (
                    irr_id TEXT PRIMARY KEY,
                    payload TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    closed_at TEXT,
                    final_hash TEXT
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    irr_id TEXT NOT NULL,
                    event_type TEXT NOT NULL,
                    data TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    prev_hash TEXT,
                    event_hash TEXT NOT NULL
                )
                """
            )
            conn.execute("CREATE INDEX IF NOT EXISTS idx_events_irr ON events(irr_id, id)")

    def _default_payload(self, irr_id: str, meta: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "irr_id": irr_id,
            "status": "open",
            "case": {
                "court": meta.get("court", "Órgano judicial DEMO"),
                "resolution_type": meta.get("resolution_type", "Sentencia"),
                "case_reference": meta.get("case_reference", "DEMO/2026"),
                "domain": meta.get("domain", "civil"),
                "demo_only": bool(meta.get("demo_only", True)),
            },
            "system": {
                "integration": meta.get("integration", "KENDOJ"),
                "provider": meta.get("provider", "Institucional (simulado)"),
                "model": meta.get("model", "Modelo institucional DEMO"),
                "version": meta.get("version", "demo-1.0"),
                "deployment_date": meta.get("deployment_date", "2026-09-18"),
                "purpose": meta.get("purpose", "Asistencia jurisdiccional autorizada (simulación)"),
                "repositories": meta.get("repositories", ["CENDOJ / repositorio oficial (simulado)"]),
                "provenance_marker": meta.get("provenance_marker", "DEMO-PROVENANCE"),
            },
            "assistance": {
                "usage_type": meta.get("usage_type", "partial_draft"),
                "segments": [],
                "materiality": {field: False for field in MATERIALITY_FIELDS},
                "assessment": {},
            },
            "sources": [],
            "alerts": [],
            "measures": [],
            "ratification": {
                "personal_complete_critical_review": False,
                "reasoning_adopted": False,
                "sources_reviewed": False,
                "alerts_resolved": False,
                "additional_justification": "",
            },
            "access": {
                "default_layer": 1,
                "preservation": False,
                "retention_policy": "Demo: no define plazo jurídico real",
            },
            "limitations": [
                "No certifica corrección material ni comprensión subjetiva.",
                "No registra teclas, tiempos de edición ni métricas de productividad.",
                "No conserva prompts completos por defecto.",
                "No está conectado a KENDOJ, Delfos, CENDOJ ni a un expediente real.",
            ],
        }

    def _load(self, irr_id: str, conn: sqlite3.Connection) -> Dict[str, Any]:
        row = conn.execute("SELECT payload FROM cases WHERE irr_id=?", (irr_id,)).fetchone()
        if not row:
            raise KeyError(f"IRR desconocido: {irr_id}")
        return json.loads(row["payload"])

    def _save(self, irr_id: str, payload: Dict[str, Any], conn: sqlite3.Connection) -> None:
        conn.execute(
            "UPDATE cases SET payload=?, updated_at=? WHERE irr_id=?",
            (canonical_json(payload), utc_now(), irr_id),
        )

    def _append_event(self, irr_id: str, event_type: str, data: Dict[str, Any], conn: sqlite3.Connection) -> Dict[str, Any]:
        last = conn.execute(
            "SELECT event_hash FROM events WHERE irr_id=? ORDER BY id DESC LIMIT 1", (irr_id,)
        ).fetchone()
        prev_hash = last["event_hash"] if last else "GENESIS"
        timestamp = utc_now()
        event_payload = {
            "irr_id": irr_id,
            "event_type": event_type,
            "data": data,
            "created_at": timestamp,
            "prev_hash": prev_hash,
        }
        event_hash = sha256_text(prev_hash + canonical_json(event_payload))
        cur = conn.execute(
            "INSERT INTO events(irr_id,event_type,data,created_at,prev_hash,event_hash) VALUES(?,?,?,?,?,?)",
            (irr_id, event_type, canonical_json(data), timestamp, prev_hash, event_hash),
        )
        return {
            "id": cur.lastrowid,
            "event_type": event_type,
            "data": data,
            "created_at": timestamp,
            "prev_hash": prev_hash,
            "event_hash": event_hash,
        }

    def create_case(self, **meta: Any) -> Dict[str, Any]:
        with self._lock, self._connect() as conn:
            irr_id = "irr_" + uuid.uuid4().hex[:16]
            payload = self._default_payload(irr_id, meta)
            now = utc_now()
            conn.execute(
                "INSERT INTO cases(irr_id,payload,created_at,updated_at) VALUES(?,?,?,?)",
                (irr_id, canonical_json(payload), now, now),
            )
            self._append_event(
                irr_id,
                "draft_created",
                {
                    "case_reference": payload["case"]["case_reference"],
                    "system": payload["system"],
                    "purpose": payload["system"]["purpose"],
                },
                conn,
            )
            assessment = assess_materiality(
                payload["assistance"]["usage_type"], payload["case"]["domain"], payload["assistance"]["materiality"]
            )
            payload["assistance"]["assessment"] = assessment
            self._save(irr_id, payload, conn)
            return self.get_case(irr_id, conn=conn)

    def get_case(self, irr_id: str, conn: Optional[sqlite3.Connection] = None) -> Dict[str, Any]:
        owns = conn is None
        if owns:
            conn = self._connect()
        assert conn is not None
        try:
            payload = self._load(irr_id, conn)
            events = conn.execute(
                "SELECT id,event_type,data,created_at,prev_hash,event_hash FROM events WHERE irr_id=? ORDER BY id",
                (irr_id,),
            ).fetchall()
            payload["events"] = [
                {
                    "id": r["id"],
                    "event_type": r["event_type"],
                    "data": json.loads(r["data"]),
                    "created_at": r["created_at"],
                    "prev_hash": r["prev_hash"],
                    "event_hash": r["event_hash"],
                }
                for r in events
            ]
            payload["integrity"] = {
                "event_count": len(events),
                "chain_head": events[-1]["event_hash"] if events else None,
            }
            return payload
        finally:
            if owns:
                conn.close()

    def register_assistance(
        self,
        irr_id: str,
        usage_type: str,
        segment_text: str = "",
        provenance: str = "institutional",
        action: str = "incorporated",
    ) -> Dict[str, Any]:
        if usage_type not in USAGE_BASELINE:
            raise ValueError("Tipo de asistencia no válido")
        if provenance not in {"institutional", "external", "unknown"}:
            raise ValueError("Procedencia no válida")
        if action not in {"incorporated", "rewritten", "discarded"}:
            raise ValueError("Acción no válida")

        with self._lock, self._connect() as conn:
            payload = self._load(irr_id, conn)
            if payload["status"] == "closed":
                raise ValueError("El IRR está cerrado")
            payload["assistance"]["usage_type"] = usage_type
            if segment_text:
                segment = {
                    "segment_id": "seg_" + uuid.uuid4().hex[:10],
                    "fingerprint": sha256_text(segment_text),
                    "preview": segment_text[:240],
                    "provenance": provenance,
                    "action": action,
                }
                payload["assistance"]["segments"].append(segment)
                self._append_event(
                    irr_id,
                    "segment_imported" if provenance != "institutional" else "segment_registered",
                    {k: v for k, v in segment.items() if k != "preview"},
                    conn,
                )
                if provenance in {"external", "unknown"}:
                    payload["assistance"]["materiality"]["alerts_or_external_imports"] = True
            assessment = assess_materiality(
                usage_type,
                payload["case"]["domain"],
                payload["assistance"]["materiality"],
            )
            payload["assistance"]["assessment"] = assessment
            self._save(irr_id, payload, conn)
            return payload

    def set_materiality(self, irr_id: str, factors: Dict[str, bool], domain: Optional[str] = None) -> Dict[str, Any]:
        with self._lock, self._connect() as conn:
            payload = self._load(irr_id, conn)
            for field in MATERIALITY_FIELDS:
                if field in factors:
                    payload["assistance"]["materiality"][field] = bool(factors[field])
            if domain:
                payload["case"]["domain"] = domain
            assessment = assess_materiality(
                payload["assistance"]["usage_type"],
                payload["case"]["domain"],
                payload["assistance"]["materiality"],
            )
            payload["assistance"]["assessment"] = assessment
            self._append_event(
                irr_id,
                "materiality_assessed",
                {
                    "level": assessment["level"],
                    "active_factors": assessment["active_factors"],
                    "domain": payload["case"]["domain"],
                },
                conn,
            )
            self._save(irr_id, payload, conn)
            return assessment

    def check_source(
        self,
        irr_id: str,
        identifier: str,
        repository: str,
        checks: Dict[str, bool],
        proposition: str = "",
        notes: str = "",
    ) -> Dict[str, Any]:
        with self._lock, self._connect() as conn:
            payload = self._load(irr_id, conn)
            clean_checks = {key: bool(checks.get(key, False)) for key in SOURCE_CHECKS}
            source = {
                "source_id": "src_" + uuid.uuid4().hex[:10],
                "identifier": identifier,
                "repository": repository,
                "proposition": proposition,
                "checks": clean_checks,
                "notes": notes,
                "checked_at": utc_now(),
            }
            payload["sources"].append(source)
            self._append_event(
                irr_id,
                "source_checked",
                {
                    "source_id": source["source_id"],
                    "identifier": identifier,
                    "repository": repository,
                    "verification_level": [k for k, v in clean_checks.items() if v],
                    "result": "partial" if not all(clean_checks.values()) else "complete",
                },
                conn,
            )
            self._save(irr_id, payload, conn)
            return source

    def register_alert(self, irr_id: str, alert_type: str, severity: str, description: str) -> Dict[str, Any]:
        if alert_type not in ALERT_TYPES:
            raise ValueError("Tipo de alerta no válido")
        if severity not in {"low", "medium", "high", "critical"}:
            raise ValueError("Severidad no válida")
        with self._lock, self._connect() as conn:
            payload = self._load(irr_id, conn)
            alert = {
                "alert_id": "alt_" + uuid.uuid4().hex[:10],
                "type": alert_type,
                "severity": severity,
                "description": description,
                "status": "open",
                "resolution": "",
            }
            payload["alerts"].append(alert)
            payload["assistance"]["materiality"]["alerts_or_external_imports"] = True
            payload["assistance"]["assessment"] = assess_materiality(
                payload["assistance"]["usage_type"],
                payload["case"]["domain"],
                payload["assistance"]["materiality"],
            )
            self._append_event(
                irr_id,
                "alert_raised",
                {"alert_id": alert["alert_id"], "type": alert_type, "severity": severity},
                conn,
            )
            self._save(irr_id, payload, conn)
            return alert

    def resolve_alert(self, irr_id: str, alert_id: str, action: str, resolution: str) -> Dict[str, Any]:
        if action not in {"corrected", "deleted", "additional_check", "primary_source", "incident_reported", "accepted_with_reason"}:
            raise ValueError("Acción de resolución no válida")
        with self._lock, self._connect() as conn:
            payload = self._load(irr_id, conn)
            target = next((a for a in payload["alerts"] if a["alert_id"] == alert_id), None)
            if not target:
                raise KeyError("Alerta desconocida")
            target["status"] = "resolved"
            target["resolution"] = resolution
            target["action"] = action
            measure = {
                "measure_id": "mea_" + uuid.uuid4().hex[:10],
                "alert_id": alert_id,
                "action": action,
                "description": resolution,
            }
            payload["measures"].append(measure)
            self._append_event(
                irr_id,
                "alert_resolved",
                {"alert_id": alert_id, "action": action},
                conn,
            )
            if action == "incident_reported":
                self._append_event(
                    irr_id,
                    "incident_reported",
                    {"category": target["type"], "severity": target["severity"], "effect": resolution, "channel": "demo"},
                    conn,
                )
            self._save(irr_id, payload, conn)
            return target

    def set_ratification(self, irr_id: str, values: Dict[str, Any]) -> Dict[str, Any]:
        allowed = {
            "personal_complete_critical_review",
            "reasoning_adopted",
            "sources_reviewed",
            "alerts_resolved",
            "additional_justification",
        }
        with self._lock, self._connect() as conn:
            payload = self._load(irr_id, conn)
            for key in allowed:
                if key in values:
                    payload["ratification"][key] = values[key] if key == "additional_justification" else bool(values[key])
            self._append_event(
                irr_id,
                "ratification_updated",
                {
                    k: v
                    for k, v in payload["ratification"].items()
                    if k != "additional_justification"
                },
                conn,
            )
            self._save(irr_id, payload, conn)
            return payload["ratification"]

    def set_preservation(self, irr_id: str, enabled: bool, reason: str = "") -> Dict[str, Any]:
        with self._lock, self._connect() as conn:
            payload = self._load(irr_id, conn)
            payload["access"]["preservation"] = bool(enabled)
            if enabled:
                self._append_event(
                    irr_id,
                    "evidence_preserved",
                    {"reason": reason or "Alegación fundada / preservación demo", "scope": "IRR relevante", "authority": "DEMO"},
                    conn,
                )
            self._save(irr_id, payload, conn)
            return payload["access"]

    def closure_blockers(self, payload: Dict[str, Any]) -> List[str]:
        blockers: List[str] = []
        assessment = payload["assistance"].get("assessment") or assess_materiality(
            payload["assistance"]["usage_type"],
            payload["case"]["domain"],
            payload["assistance"]["materiality"],
        )
        level = assessment["level"]
        rat = payload["ratification"]

        if not rat.get("personal_complete_critical_review"):
            blockers.append("Falta declaración de revisión personal, completa y crítica.")
        if not rat.get("reasoning_adopted"):
            blockers.append("Falta adopción humana del razonamiento final.")

        unresolved = [a for a in payload["alerts"] if a["status"] != "resolved"]
        if unresolved:
            blockers.append(f"Existen {len(unresolved)} alerta(s) sin resolver.")

        required = required_source_checks(level)
        if required:
            if not payload["sources"]:
                blockers.append("El nivel exige verificación de fuentes y no consta ninguna fuente verificada.")
            else:
                for src in payload["sources"]:
                    missing = [c for c in required if not src["checks"].get(c)]
                    if missing:
                        blockers.append(
                            f"Fuente {src['identifier']} incompleta: faltan " + ", ".join(missing)
                        )

        if level in {"extended", "reinforced"} and not rat.get("sources_reviewed"):
            blockers.append("Debe confirmarse la revisión de las fuentes relevantes.")
        if level in {"extended", "reinforced"} and not rat.get("alerts_resolved"):
            blockers.append("Debe confirmarse que las incidencias relevantes han sido resueltas.")
        if level == "reinforced" and not str(rat.get("additional_justification", "")).strip():
            blockers.append("El nivel reforzado exige una justificación adicional breve.")

        return blockers

    def close(self, irr_id: str) -> CloseResult:
        with self._lock, self._connect() as conn:
            payload = self._load(irr_id, conn)
            blockers = self.closure_blockers(payload)
            if blockers:
                return CloseResult(False, blockers, self.get_case(irr_id, conn=conn))

            payload["status"] = "closed"
            closed_at = utc_now()
            payload["closed_at"] = closed_at
            event = self._append_event(
                irr_id,
                "irr_closed",
                {
                    "level": payload["assistance"]["assessment"]["level"],
                    "ratification": {
                        "personal_complete_critical_review": True,
                        "reasoning_adopted": True,
                    },
                },
                conn,
            )
            final_material = canonical_json(payload) + event["event_hash"]
            final_hash = sha256_text(final_material)
            payload["final_integrity_hash"] = final_hash
            conn.execute(
                "UPDATE cases SET payload=?, updated_at=?, closed_at=?, final_hash=? WHERE irr_id=?",
                (canonical_json(payload), closed_at, closed_at, final_hash, irr_id),
            )
            return CloseResult(True, [], self.get_case(irr_id, conn=conn))

    def process_tool(self, name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        if name == "irr_create_case":
            return self.create_case(**arguments)
        if name == "irr_register_assistance":
            return self.register_assistance(**arguments)
        if name == "irr_assess_materiality":
            irr_id = arguments.pop("irr_id")
            factors = arguments.pop("factors", {})
            domain = arguments.pop("domain", None)
            return self.set_materiality(irr_id, factors, domain)
        if name == "irr_check_source":
            return self.check_source(**arguments)
        if name == "irr_register_alert":
            return self.register_alert(**arguments)
        if name == "irr_resolve_alert":
            return self.resolve_alert(**arguments)
        if name == "irr_set_ratification":
            irr_id = arguments.pop("irr_id")
            return self.set_ratification(irr_id, arguments)
        if name == "irr_preserve_evidence":
            return self.set_preservation(**arguments)
        if name == "irr_get_report":
            return self.get_case(arguments["irr_id"])
        if name == "irr_close":
            result = self.close(arguments["irr_id"])
            return {"closed": result.closed, "blockers": result.blockers, "report": result.report}
        raise KeyError(f"Herramienta MCP desconocida: {name}")
