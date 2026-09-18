# IRR Guard · MCP + Wizard demo

Prototipo funcional de investigación basado en el **Informe de Ratificación Razonada (IRR)**. Su objetivo es demostrar cómo el IRR puede funcionar como una capa de trazabilidad y supervisión humana entre una herramienta judicial asistencial (p. ej., KENDOJ o Delfos) y el cierre de una resolución.

> **Importante:** no está conectado a KENDOJ, Delfos, CENDOJ ni a ningún expediente judicial real. Las integraciones son simuladas porque el prototipo no dispone de API, credenciales, contrato institucional ni SSO de esos sistemas. No debe utilizarse con datos reales sin revisión de seguridad, protección de datos, interoperabilidad y gobernanza.

## Qué implementa del artículo

1. **Cinco bloques funcionales:** identificación/finalidad; procedencia/incidencia; verificación de fuentes; riesgos/incidencias; ratificación razonada.
2. **Proporcionalidad:** búsqueda → mínimo; resumen → básico; borrador parcial → extendido; borrador íntegro → reforzado.
3. **Test de incidencia material:** ratio decidendi, hechos/prueba, subsunción/fallo, derechos fundamentales, nuevas fuentes/argumentos, riesgo de omisión, alertas/importaciones y alegación fundada.
4. **Verificación material por capas:** sintaxis ≠ existencia ≠ correspondencia ≠ fidelidad de la proposición ≠ vigencia ≠ ratio/obiter ≠ contradicción ≠ fidelidad al expediente.
5. **Pausa deliberativa:** cierre bloqueado solo por incidencias objetivas pendientes y requisitos proporcionales al nivel.
6. **Integridad:** cadena SHA-256 de eventos significativos y huella final de cierre.
7. **Minimización:** no registra teclas, tiempos, navegación, prompts completos ni scores de productividad.
8. **Acceso por capas:** la interfaz recuerda los cuatro niveles conceptuales del artículo.

## Arquitectura

```text
KENDOJ / Delfos / otra herramienta (simulada)
               │
               ▼
       ┌──────────────────┐
       │   IRR Guard MCP  │  /mcp
       │  tools + policy  │
       └────────┬─────────┘
                │ mismos casos / eventos
       ┌────────▼─────────┐
       │   IRR Core       │
       │ materiality      │
       │ source checks    │
       │ alerts / close   │
       │ hash chain       │
       └────────┬─────────┘
                │
       ┌────────▼─────────┐
       │ SQLite local     │
       └──────────────────┘
                │
       ┌────────▼─────────┐
       │ Wizard web demo  │  /
       └──────────────────┘
```


## Código abierto y cita académica

El código de este prototipo se publica bajo licencia **MIT**. La licencia del software no modifica los derechos o condiciones de publicación del artículo académico subyacente. Véanse `LICENSE`, `NOTICE.md` y `CITATION.cff`.

La rama `main` incluye un workflow de smoke tests y una landing preparada para **GitHub Pages** en `docs/`.

## Ejecutar la demo

Requiere Python 3.10+.

```bash
python -m venv .venv
source .venv/bin/activate       # Windows: .venv\\Scripts\\activate
pip install -r requirements.txt
./run_demo.sh
```

O, para lanzar servidor y navegador con un solo comando:

```bash
python launch.py
```

Abrir: `http://127.0.0.1:8787`

## MCP

Endpoint: `http://127.0.0.1:8787/mcp`

El servidor autocontenido implementa el subconjunto `tools` de **MCP 2026-07-28** (stateless: `server/discover`, `tools/list`, `tools/call`) y mantiene compatibilidad básica con el flujo de inicialización `2025-06-18`. Para producción se recomienda sustituir esta implementación compacta por el SDK oficial MCP v2 y añadir autenticación/autorización institucional, límites, logging de seguridad y pruebas de conformidad.

Herramientas:

- `irr_create_case`
- `irr_register_assistance`
- `irr_assess_materiality`
- `irr_check_source`
- `irr_register_alert`
- `irr_resolve_alert`
- `irr_set_ratification`
- `irr_preserve_evidence`
- `irr_get_report`
- `irr_close`

Smoke test MCP, con el servidor arrancado:

```bash
python demo_mcp_client.py
```

También se incluye un adaptador **stdio** autocontenido:

```bash
python mcp_stdio.py
```

Con un Inspector que soporte MCP actual, puede usarse el comando anterior como servidor stdio.

## Guion de demo (3–4 minutos)

1. **“Esto no es otro LLM: es una capa de control.”** Cargar el escenario de charla y abrir un IRR sobre KENDOJ.
2. Registrar **borrador parcial**. Mostrar que se guarda la procedencia/huella, no el prompt.
3. Activar **derechos fundamentales** + **nuevas fuentes**: el IRR pasa a **reforzado** y explica por qué, sin score.
4. Verificar una fuente por capas. Subrayar que “ECLI válido” no equivale a “proposición correcta”.
5. Crear una incidencia de alucinación/contradicción y avanzar: la pausa muestra que el cierre debe quedar bloqueado.
6. Resolverla con fuente primaria, marcar revisión/adopción y cerrar.
7. Enseñar el JSON final y la **cadena de integridad**. Mensaje final: “la firma atribuye; la motivación justifica; el IRR documenta la supervisión”.

## Camino a una integración institucional real

- Adaptador de identidad/SSO y roles.
- API/document events de KENDOJ/Delfos o integración en el editor/gestor procesal autorizado.
- Resolución real contra repositorios oficiales y versionados.
- WORM / sellado temporal cualificado o servicio institucional de evidencia.
- Cifrado, segregación por expediente y control de acceso por capas.
- DPIA/EIPD, evaluación de impacto en derechos fundamentales y threat model técnico.
- Canal institucional de incidentes y monitorización agregada **sin perfilado individual**.
- Política de retención/preservación coordinada con recursos y expediente electrónico.
- Validación de usabilidad, falsos positivos, carga cognitiva y accesibilidad antes de efectos jurídicos.

## Nota metodológica

El artículo propone el test y los niveles, pero no un algoritmo numérico validado. Por eso este prototipo usa **reglas transparentes y conservadoras** y muestra su razonamiento. No debe convertirse en un “risk score” del juez ni en una presunción de diligencia/negligencia.

## Publicación / QR

Para publicar el MVP como repositorio abierto y generar el QR de la charla, véase `PUBLISH_TO_GITHUB.md`. Se recomienda que el QR apunte a la landing de **GitHub Pages** y que desde ella se ofrezca el repositorio y la descarga del código.
