# Diseño IRR → componentes del prototipo

| Principio IRR | Implementación demo |
|---|---|
| Identificación y finalidad | `draft_created` + metadatos de sistema/modelo/versión/finalidad |
| Procedencia e incidencia | huella SHA-256 por segmento + procedencia + tipo de asistencia |
| Test de incidencia material | motor de reglas explicable en `assess_materiality()` |
| Verificación material | 8 comprobaciones independientes por fuente |
| Riesgos e incidencias | alertas tipadas + medida de resolución + posible escalado |
| Ratificación razonada | cuatro confirmaciones + justificación si reforzado |
| Pausa adaptativa | `closure_blockers()`; bloquea solo si faltan requisitos objetivos |
| Integridad | hash encadenado de eventos + `final_integrity_hash` |
| Minimización | no keystrokes, no tiempo de edición, no historial de navegación, no prompt completo |
| No vigilancia | ningún ranking, score de juez ni métrica individual |
| Preservación | evento `evidence_preserved` separado del fondo del asunto |
| Acceso escalonado | representado conceptualmente en la pantalla final |

## Punto de inserción sobre KENDOJ/Delfos

El patrón buscado es un **sidecar/gateway**: la herramienta asistencial envía a IRR Guard eventos mínimos (`segment_registered`, `source_checked`, `alert_raised`...), y antes de firmar consulta `irr_close`. La decisión sustantiva sigue fuera del MCP. IRR Guard no decide el caso; únicamente devuelve si la traza exigible está completa o qué incidencia objetiva falta.

En un despliegue institucional, los conectores serían adaptadores autenticados a eventos y repositorios oficiales. Este repositorio usa un mock deliberadamente para no fingir acceso a APIs no públicas.
