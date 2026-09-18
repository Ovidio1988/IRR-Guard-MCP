from __future__ import annotations

TOOLS = [
    {
        "name": "irr_create_case",
        "title": "Abrir IRR",
        "description": "Abre un IRR para una resolución asistida. Devuelve un irr_id explícito que debe pasarse a las llamadas posteriores.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "court": {"type": "string"},
                "resolution_type": {"type": "string"},
                "case_reference": {"type": "string"},
                "domain": {"type": "string", "enum": ["civil", "criminal", "social", "administrative", "sanctioning", "family_minors", "detention", "asylum_immigration", "discrimination"]},
                "integration": {"type": "string", "enum": ["KENDOJ", "DELFOS", "MOCK"]},
                "model": {"type": "string"},
                "version": {"type": "string"},
                "purpose": {"type": "string"}
            },
            "required": ["case_reference", "integration"]
        },
        "annotations": {"readOnlyHint": False, "destructiveHint": False, "idempotentHint": False}
    },
    {
        "name": "irr_register_assistance",
        "title": "Registrar asistencia IA",
        "description": "Registra el tipo de asistencia y, opcionalmente, la huella de un segmento. No conserva el prompt completo.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "irr_id": {"type": "string"},
                "usage_type": {"type": "string", "enum": ["search", "summary", "partial_draft", "full_draft", "other"]},
                "segment_text": {"type": "string", "description": "Solo para demo; se guarda huella y una vista previa limitada."},
                "provenance": {"type": "string", "enum": ["institutional", "external", "unknown"]},
                "action": {"type": "string", "enum": ["incorporated", "rewritten", "discarded"]}
            },
            "required": ["irr_id", "usage_type"]
        }
    },
    {
        "name": "irr_assess_materiality",
        "title": "Aplicar test de incidencia material",
        "description": "Aplica una traducción conservadora y explicable del test IRR; no genera una puntuación de diligencia.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "irr_id": {"type": "string"},
                "domain": {"type": "string"},
                "factors": {
                    "type": "object",
                    "properties": {
                        "ratio_decidendi": {"type": "boolean"},
                        "facts_or_evidence": {"type": "boolean"},
                        "subsumption_or_ruling": {"type": "boolean"},
                        "fundamental_rights": {"type": "boolean"},
                        "new_sources_or_arguments": {"type": "boolean"},
                        "omission_risk": {"type": "boolean"},
                        "alerts_or_external_imports": {"type": "boolean"},
                        "challenged_by_party": {"type": "boolean"}
                    },
                    "additionalProperties": False
                }
            },
            "required": ["irr_id", "factors"]
        }
    },
    {
        "name": "irr_check_source",
        "title": "Verificar fuente",
        "description": "Registra la verificación material por capas: existencia, correspondencia, fidelidad, vigencia, ratio/obiter, contradicción y expediente.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "irr_id": {"type": "string"},
                "identifier": {"type": "string"},
                "repository": {"type": "string"},
                "proposition": {"type": "string"},
                "notes": {"type": "string"},
                "checks": {
                    "type": "object",
                    "properties": {
                        "identifier_syntax": {"type": "boolean"},
                        "existence": {"type": "boolean"},
                        "document_match": {"type": "boolean"},
                        "proposition_fidelity": {"type": "boolean"},
                        "temporal_validity": {"type": "boolean"},
                        "ratio_obiter": {"type": "boolean"},
                        "contrary_authority": {"type": "boolean"},
                        "record_fidelity": {"type": "boolean"}
                    },
                    "additionalProperties": False
                }
            },
            "required": ["irr_id", "identifier", "repository", "checks"]
        }
    },
    {
        "name": "irr_register_alert",
        "title": "Registrar incidencia",
        "description": "Registra una incidencia o alerta relevante sin atribuir automáticamente negligencia al usuario.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "irr_id": {"type": "string"},
                "alert_type": {"type": "string", "enum": ["hallucination", "contradiction", "omission", "personal_data", "bias", "prompt_injection", "external_import", "model_change", "source_manipulation", "verifier_error", "other"]},
                "severity": {"type": "string", "enum": ["low", "medium", "high", "critical"]},
                "description": {"type": "string"}
            },
            "required": ["irr_id", "alert_type", "severity", "description"]
        }
    },
    {
        "name": "irr_resolve_alert",
        "title": "Resolver incidencia",
        "description": "Documenta la medida adoptada ante una incidencia: corrección, eliminación, contraste, fuente primaria o escalado.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "irr_id": {"type": "string"},
                "alert_id": {"type": "string"},
                "action": {"type": "string", "enum": ["corrected", "deleted", "additional_check", "primary_source", "incident_reported", "accepted_with_reason"]},
                "resolution": {"type": "string"}
            },
            "required": ["irr_id", "alert_id", "action", "resolution"]
        }
    },
    {
        "name": "irr_set_ratification",
        "title": "Ratificación razonada",
        "description": "Registra la revisión personal, completa y crítica y la adopción humana del razonamiento. El nivel reforzado exige justificación breve.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "irr_id": {"type": "string"},
                "personal_complete_critical_review": {"type": "boolean"},
                "reasoning_adopted": {"type": "boolean"},
                "sources_reviewed": {"type": "boolean"},
                "alerts_resolved": {"type": "boolean"},
                "additional_justification": {"type": "string"}
            },
            "required": ["irr_id"]
        }
    },
    {
        "name": "irr_preserve_evidence",
        "title": "Preservar evidencia",
        "description": "Activa preservación de la trazabilidad relevante ante una alegación fundada, sin prejuzgar el fondo.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "irr_id": {"type": "string"},
                "enabled": {"type": "boolean"},
                "reason": {"type": "string"}
            },
            "required": ["irr_id", "enabled"]
        }
    },
    {
        "name": "irr_get_report",
        "title": "Obtener IRR",
        "description": "Devuelve el IRR completo, su cadena de eventos y la huella de integridad disponible.",
        "inputSchema": {"type": "object", "properties": {"irr_id": {"type": "string"}}, "required": ["irr_id"]},
        "annotations": {"readOnlyHint": True, "destructiveHint": False, "idempotentHint": True}
    },
    {
        "name": "irr_close",
        "title": "Cerrar IRR",
        "description": "Ejecuta la pausa deliberativa de cierre. Bloquea solo por incidencias objetivas pendientes según el nivel IRR.",
        "inputSchema": {"type": "object", "properties": {"irr_id": {"type": "string"}}, "required": ["irr_id"]}
    }
]
