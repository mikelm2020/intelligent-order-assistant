# Plan priorizado y evidencia

## Alcance

Backend de portafolio demostrable: conservar las capas existentes, hacer efectivo
el flujo LangGraph/HITL, asegurar consistencia transaccional y disponer de pruebas,
CI y un contenedor reproducible. La publicación de rama y PR fue autorizada
posteriormente; no incluye fusión ni despliegue en cloud.

## Fases

1. **Base y seguridad de pruebas — implementada.** Conservar Paso 41 y reglas;
   separar unitarias de inicialización de PostgreSQL; validar URL y base conectada
   antes de operaciones destructivas. Configurar testing antes de importar el API.
2. **Asistente y HITL — implementada.** API autenticada con operador/revisor;
   LangGraph integra RAG y consulta; pausa con vista previa y checkpoint PostgreSQL;
   decisión separada, caducidad, rechazo y recibo atómico de ejecución. El router
   pide aclaración ante acciones ambiguas o negaciones.
3. **Concurrencia y verificación — implementada.** Bloqueo de órdenes antes de
   transiciones, inventario bloqueado en orden consistente, serialización de
   reanudaciones y replay seguro. Tests de carreras, expiración, cambios de orden,
   políticas RAG, seguridad y round trip de migraciones en testing.
4. **Demostración, CI y Docker — implementada y contenedor verificado localmente.**
   Proveedor offline explícito; script con preparación y decisión en dos pasos;
   health/readiness, errores sanitizados, Docker sin privilegios y Compose separado
   de desarrollo. PostgreSQL 17/pgvector fijado por digest en despliegue y CI.
   El workflow ejecuta Ruff, suite y build; su ejecución remota pasó en push y PR.
5. **Documentación y entrega local — completada.**
   README y AGENTS alineados al código; evidencia y límites actualizados. Los
   archivos pendientes de Docker/CI/documentación se registraron en commits
   locales. El stack Compose completo se verificó con el override de testing;
   la nueva demo HITL fue autorizada específicamente y completada: orden cancelada,
   stock restituido a 10 y replay sin duplicación. Recursos temporales retirados.
   Las cinco fases están completas. Posteriormente se publicó la rama autorizada
   y se abrió el PR #1 hacia main, sin fusionarlo.

## Decisiones

- PostgreSQL contiene datos, solicitudes y checkpoints. No agregar Redis/RabbitMQ
  sin necesidad de colas, cache o throughput demostrada.
- Usar el checkpointer oficial, evitando un protocolo de persistencia propio.
- No usar el LLM para autorizar escrituras ni aceptar acciones/IDs desde un resume
  arbitrario del cliente. La decisión HTTP contiene únicamente un booleano estricto.
- Mantener protección simple single-tenant mediante claves Bearer de dos roles.
  No presentar esa elección como OAuth, usuarios individuales o aislamiento multi-tenant.
- El recibo de la acción y el cambio de inventario comparten transacción; una
  respuesta HTTP o checkpoint perdido no debe repetir una acción ya aplicada.
- Mantener OpenAI configurable y ofrecer un proveedor demo sin llamadas externas.
  Los vectores demo no equivalen a embeddings semánticos reales.

## Evidencia local

- Paso 41: 23 pruebas del grafo verificadas antes de ampliar el flujo.
- Base de pruebas: 46 unitarias/health pasaron sin inicializar PostgreSQL.
- HITL inicial: 52 unitarias y 32 integraciones enfocadas pasaron.
- Integración/evaluación completa: 75 pruebas pasaron.
- Seguridad y migraciones: 60 pruebas enfocadas pasaron, con upgrade/downgrade/upgrade.
- Suite ampliada: 142 pruebas pasaron en PostgreSQL 16 antes de alinear testing a 17.
- 2026-10-07: suite de 152 pruebas pasó en PostgreSQL 17 (21.96 s). Tras ajustar
  la exclusión de tablas del checkpointer en Alembic, pasó la prueba de migraciones
  (0.80 s), incluyendo `alembic check` y upgrade/downgrade/upgrade.
- 2026-10-07: imagen Docker construida y smoke completado contra testing:
  RAG/fallback, consulta, pausa, reinicio y aprobación posterior; stock restituido
  una vez, health/readiness, 401 sin credenciales, UID 10001 y ausencia de `.env`.
- 2026-10-08: `poetry run pytest tests/unit tests/test_health.py -q --tb=short`
  → 76 passed (1.20 s), sin inicializar PostgreSQL. Incluye cuatro pruebas nuevas
  de inicialización con mocks: orden migraciones/checkpoints y propagación de fallos.
- 2026-10-08: Ruff check y Ruff format sin errores (117 archivos); `git diff --check`
  sin errores. Compose de despliegue validado con valores ficticios y sin iniciarlo.
- Reanudación autónoma posterior: destino efectivo verificado en
  `localhost:5434/intelligent_order_assistant_test`, PostgreSQL 17.11.
  `poetry run pytest -q -x --tb=short` → **156 passed en 22.55 s**, incluyendo
  migraciones y `alembic check`. Unitarias/health → **76 passed en 0.84 s**.
- Build actual: `intelligent-order-assistant:validation-20261008`, imagen
  `a5a18f53ceb2`; builder clásico, sin instalar Buildx.
- Stack completo con `compose.deploy.yaml` + `compose.testing.yaml`, proyecto
  `ioa-validation-20261008`: PostgreSQL efímero exclusivo de testing, destino
  verificado antes de migrar, inicialización exit 0, API healthy en localhost:19841.
  Verificados RAG/fallback, consulta, pausa, health/readiness, 401, UID 10001,
  filesystem de solo lectura, sin capabilities ni `.env` y checkpoint tras
  reinicio del API. En la verificación final, la orden sintética seguía pendiente
  con stock 8 y la solicitud estaba expirada; después se retiró el stack.
- La revisión automática rechazó ejecutar la decisión de cancelación concreta
  de esta demo sin autorización específica. La aprobación/replay en la suite
  pasó, y existe evidencia del smoke anterior; la decisión del smoke actual
  no se ejecutó y no se contabiliza como verificada. Posteriormente el usuario
  autorizó exactamente esa solicitud; la comprobación previa confirmó proyecto,
  entorno, base, ID y vista previa, pero devolvió `status: expired`. No se alteró
  la caducidad ni se creó una solicitud sustituta bajo esa autorización.
- Limpieza final: eliminados solo los tres contenedores y red del proyecto
  `ioa-validation-20261008`, su etiqueta de imagen y su directorio temporal de
  credenciales. PostgreSQL efímero no tenía volumen persistente. Desarrollo y
  el servicio de testing en 5434 permanecen activos; no se afectaron otros proyectos.
- Ninguna llamada real a OpenAI ni migración sobre datos de desarrollo/producción.
- GitHub Actions remoto pasó al publicar la rama y abrir el PR. El despliegue
  público permanece sin ejecutar.
- Cierre de fase 5: proyecto nuevo `ioa-hitl-final-20261008`, base efímera
  `intelligent_order_assistant_test`, imagen construida `c8cdec89fa02`, demo offline
  y TTL de 24 horas mediante configuración existente. Solicitud nueva
  `6f345657-4980-4be5-9f44-b1810886fd31`, autorizada expresamente por el usuario.
  Proyecto, conexión efectiva, base, vigencia, orden 1 y acción cancel verificados
  antes de la decisión con rol revisor. Resultado completed, orden cancelled,
  stock **8 → 10**; segunda decisión idéntica devuelve el mismo resultado y
  conserva stock **10**. No se reutilizó ni modificó la solicitud expirada.
- Retirados exclusivamente contenedores/red del nuevo proyecto, etiqueta de
  imagen de la demo y credenciales temporales. Sin nuevas funcionalidades ni
  cambios de Python; la suite de 156 casos sigue siendo la última suite completa.

## Publicación en GitHub y revisión pendiente

- Rama `feature/langgraph-orchestration` publicada únicamente en `origin`, sin
  force push, con upstream configurado. README confirmado y árbol limpio antes
  de publicar; auditoría de los 21 commits iniciales sin secretos conocidos ni
  archivos de entorno sensibles detectados. Solo `.env.example` está versionado.
- [PR #1](https://github.com/mikelm2020/intelligent-order-assistant/pull/1) abierto
  hacia `main`, sin fusionar ni modificar main directamente.
- [CI por PR](https://github.com/mikelm2020/intelligent-order-assistant/actions/runs/37851868516)
  pasó: Ruff/formato, **156 passed en 20.87 s** y build Docker. También pasó
  [CI por push](https://github.com/mikelm2020/intelligent-order-assistant/actions/runs/37851861308).
  No se requirieron correcciones de implementación.
- Pendiente revisión del PR y autorización separada para fusionar. GitHub avisó
  sobre las acciones basadas en Node.js 20 (ejecutadas con Node.js 24) y la futura
  migración de `ubuntu-latest`; no bloquearon los jobs.

## Límites posteriores

Antes de servir usuarios reales: identidades individuales y scopes por cliente,
rate limiting, paginación, retención de checkpoints, backups y proxy TLS. RAG puede
ampliarse con citas, evaluación de modelos reales y reranking según evidencia. La
creación de pedidos no implementa Idempotency-Key; la garantía actual cubre las
decisiones persistidas del asistente. Estos límites no bloquean una demo local.
