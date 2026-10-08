# Estado del desarrollo

Fecha de última actualización: 2026-10-08 (America/Mexico_City).
Rama: `feature/langgraph-orchestration`.
HEAD: `cfba253`.

Desarrollo reanudado por solicitud del usuario el 2026-10-08. Se conservaron los
cambios existentes y se continuó el cierre de Docker, CI y documentación.
Autorización vigente: decisiones técnicas, edición/refactor, Ruff, unitarias,
integración exclusivamente en testing tras verificar destino, builds locales,
commits locales pequeños y documentación. No repetir solicitudes de autorización
para esas operaciones. Prohibido modificar desarrollo/producción, migrar fuera
de testing, hacer push, publicar, generar costes o afectar otros proyectos.

## Fase 1: registro de cambios pendientes (2026-10-08)

Se revisaron todos los diffs y archivos nuevos. Ruff check y formato pasaron;
unitarias/health: **76 passed en 0.84 s** fuera del sandbox. La ejecución dentro
del sandbox se bloqueó y fue interrumpida; no cuenta como resultado completo.
Compose se validó con configuración ficticia.
Los cambios se registran en grupos: inicialización y pruebas; Docker/Compose;
CI; documentación y estado. La integración y la demostración se harán después,
en secuencia y exclusivamente contra testing.

Commits de esta fase: `d5b71ac` (inicialización), `7428837` (Docker/Compose),
`b60d0bf` (CI). Documentación revisada se registra en un cuarto commit.

## Trabajo realizado al reanudar (2026-10-08)

- Se leyeron AGENTS, este registro, diffs y archivos pendientes; no se repitieron
  funcionalidades de negocio ni se descartaron cambios previos.
- Se verificó el digest registrado mediante `docker image inspect` y se fijó
  PostgreSQL 17/pgvector en `compose.deploy.yaml` y `.github/workflows/ci.yml`.
  Los servicios de desarrollo no se reemplazaron.
- Se revisaron README/AGENTS y scripts de inicialización. Se corrigió el docstring
  que confundía ejecutar el módulo con disponer de autorización para migraciones.
- Se agregaron cuatro pruebas unitarias con mocks de la inicialización: migrar
  antes de crear checkpoints, detenerse si falla Alembic, propagar errores de
  checkpoints y cerrar su contexto incluso ante un fallo.
- Se actualizó `docs/implementation-plan.md` con evidencia del contenedor y de
  PostgreSQL 17, diferenciando las verificaciones previas de las actuales.
- `poetry run pytest tests/unit tests/test_health.py -q --tb=short`:
  **76 passed en 1.20 s**, sin conexiones ni inicialización de PostgreSQL.
- `poetry run ruff check --no-cache .`: sin errores.
- `poetry run ruff format --check --no-cache .`: **117 archivos** conformes.
- `git diff --check`: sin errores.
- `docker compose --env-file /dev/null -p ioa-demo -f compose.deploy.yaml config
  --quiet`, con variables ficticias mediante `env`: correcto. Una comprobación
  inicial sin estas variables falló por falta de `DB_PASSWORD`, como exige Compose.
- No se ejecutaron integración/evaluación, migraciones, escrituras de demo,
  reconstrucción Docker, inicio del stack, CI remoto, commits ni push en esta sesión.

## Funcionalidades terminadas

- Paso 41 conservado: detección determinística de `lookup`, `confirm` y `cancel`,
  con `None` para conocimiento y pruebas de consultas sin ID.
- LangGraph integrado en `/api/v1/assistant/ask`, con rutas de RAG y pedidos.
  Se propagan `limit` y `max_distance`, manteniendo el umbral configurable y el
  fallback sin llamada al chat.
- Acciones ambiguas o negativas solicitan aclaración en lugar de ejecutarse.
- API protegida mediante credenciales Bearer distintas para operador y revisor.
  Confirmación/cancelación directa requiere el rol revisor.
- HITL con `interrupt()` y `Command(resume=...)`, usando el checkpointer oficial
  de PostgreSQL: vista previa persistida, revisión, decisión separada, rechazo,
  caducidad y prohibición de aprobar solicitudes propias.
- El cambio de una orden invalida su aprobación pendiente. Las reanudaciones
  concurrentes se serializan y el recibo de ejecución se confirma junto con la
  acción de negocio, evitando aplicar el inventario dos veces en un reintento.
- Pedidos: bloqueo de la orden antes de transiciones, actualización del estado
  desde datos refrescados y bloqueos de productos en orden consistente.
- Pruebas unitarias sin inicializar PostgreSQL. Integración/evaluación valida URL
  y `current_database()` antes de operaciones destructivas. La configuración de
  testing se establece antes de importar la aplicación.
- Migraciones verificadas con upgrade/downgrade/upgrade y `alembic check` en
  testing. Alembic excluye las tablas administradas por el checkpointer.
- Modo demo offline con vectores ilustrativos de 1536 dimensiones y respuesta
  basada en el contexto. No representa un LLM ni embeddings semánticos reales.
- Script de demostración en dos pasos: preparación y aprobación/rechazo explícito.
- Readiness, errores sanitizados de IA/base de datos y configuración de secretos
  protegida en representaciones y errores de validación.
- Imagen Docker construida y probada con usuario sin privilegios, filesystem
  de solo lectura y sin copiar `.env`. Su integración con FastAPI/HITL se verificó
  contra testing, incluyendo un reinicio antes de aprobar.

## Trabajo pendiente o incompleto

- Docker, Compose de despliegue, CI, scripts de inicialización y documentación
  están escritos, pero los archivos indicados abajo siguen sin commit.
- `docs/implementation-plan.md`, README y AGENTS revisados conjuntamente con los
  scripts y comandos de inicialización/despliegue al reanudar; siguen sin commit.
- PostgreSQL 17 está fijado en despliegue/CI con el digest verificado localmente:
  `pgvector/pgvector@sha256:cf134a767f474095eeba57e0117be8e568e011a63f33fbf252f14c9b760f8e6f`.
  Python también está fijado por digest en Dockerfile.
- El Compose de despliegue pasó validación de configuración, pero no se levantó
  el stack completo de despliegue. La prueba Docker utilizó networking de host y
  la base exclusiva de testing.
- GitHub Actions remoto, llamadas reales a OpenAI y despliegue público no se han
  ejecutado. No se hizo push.
- Límites documentados: roles compartidos single-tenant, sin identidades personales
  ni aislamiento por cliente; sin paginación, rate limiting, Idempotency-Key para
  creación de pedidos, citas estructuradas o retención de checkpoints. La garantía
  de replay implementada corresponde a decisiones del asistente.
- Redis y RabbitMQ no se agregaron: no hay un caso demostrado que los justifique.

## Archivos con cambios sin commit al pausar

Modificados:

- `.env.example`
- `AGENTS.md`
- `Dockerfile`
- `README.md`
- `compose.yaml`

Nuevos:

- `.dockerignore`
- `.github/workflows/ci.yml`
- `compose.deploy.yaml`
- `docs/implementation-plan.md`
- `scripts/initialize_database.py`
- `scripts/setup_checkpoints.py`
- `DEVELOPMENT_PROGRESS.md` (este documento)

No había cambios staged en la revisión de Git. El cambio previo de `state.py` y
el archivo inicialmente nuevo `AGENTS.md` fueron conservados en los commits
locales autorizados; ahora AGENTS contiene actualizaciones adicionales sin commit.

## Commits locales ya realizados con autorización

- `47b7042` — `feat: detect assistant order actions and document agent rules`
- `495a5c5` — `test: isolate unit tests and guard destructive database fixtures`
- `460ca3b` — `fix: serialize order transitions and acquire inventory locks consistently`
- `6f0cb35` — `feat: integrate durable LangGraph approvals with role-protected API`
- `0265f96` — `test: verify migration round trips and enforce testing-only connections`
- `ef3661f` — `feat: add offline demo providers and deployment readiness checks`
- `cfba253` — `fix: validate native checkpoint dependency and enforce approval invariants`

No se realizaron commits después de la solicitud de detener el desarrollo.

## Últimas verificaciones reales

- Suite completa: `poetry run pytest -q -x --tb=short` → **152 passed en 21.96 s**,
  sobre PostgreSQL 17 de testing, antes del último ajuste de exclusión de tablas
  del checkpointer en Alembic.
- Después de ese ajuste:
  `poetry run pytest tests/integration/migrations -q -x --tb=short` →
  **1 passed en 0.80 s**, incluyendo `alembic check` y round trip de migraciones.
- Pruebas enfocadas previas de seguridad, aprobación, readiness y demo:
  **30 passed en 4.70 s**; posteriormente incluidas en la suite ampliada.
- Últimos `ruff check`, `ruff format --check` y `git diff --check`: sin errores.
- `docker build -t intelligent-order-assistant:local .`: completado.
  Imagen final local: `ad6e37c95b61`.
- `docker compose --env-file /tmp/ioa-compose-validation.env -p ioa-demo
  -f compose.deploy.yaml config --quiet`: terminó correctamente. El archivo
  temporal contiene exclusivamente valores ficticios de validación.
- Smoke Docker final: recuperación documental, fallback, consulta, pausa,
  reinicio del API y aprobación posterior completados. Se verificaron orden
  cancelada, stock restituido a 10, health/readiness, rechazo HTTP 401 sin
  credenciales, UID 10001 y ausencia de `/app/.env`.
- Todas las migraciones y escrituras de demostración se realizaron únicamente
  sobre `intelligent_order_assistant_test` en `localhost:5434`.

## Errores encontrados y situación actual

- Asyncio se bloquea al cerrar ciertos tests dentro del sandbox. Las validaciones
  se ejecutaron fuera del sandbox con aprobación; no se modificó código para
  ocultar ese problema del entorno.
- Docker no tiene el plugin Buildx en este entorno; `docker build` funcionó con
  el builder clásico. Compose de configuración funciona. No se instaló Buildx.
- Hubo timeouts al descargar dependencias. El build pasó al ampliar timeouts y
  reducir la concurrencia de descargas de Poetry.
- La primera prueba Docker encontró ocupado el puerto 8010. Se usó el puerto
  local dedicado 19841 para la prueba final.
- Se inició por error una suite mientras la demo utilizaba la misma base de
  testing. La suite fue interrumpida; sus 14 casos parciales no se contabilizan
  como validación final. Se repitieron suite y demo en secuencia.
- El smoke detectó que FastAPI no aceptaba una dependencia decorada directamente
  con `asynccontextmanager`. Se separó el context manager de la dependencia con
  `yield` y se agregó una regresión que usa la dependencia real. Corregido y
  comprobado tanto con pruebas como en la imagen final.

El contenedor temporal `ioa-portfolio-smoke-20261007` se detuvo y retiró al terminar.
La base de testing quedó con esquema y registros sintéticos de la demo; no debe
tratarse como datos reales. No se modificó `.env` ni se migró la base de desarrollo.

## Próximos pasos que requieren autorización

1. Si se autoriza iniciar el stack y sus migraciones, verificar el destino y usar
   un proyecto separado, como `ioa-demo`, sin reemplazar desarrollo/testing.
2. Si se autoriza repetir integración/evaluación, verificar URL y base efectiva
   exclusivamente de testing. Suite y demo deben ejecutarse en secuencia.
3. Con autorización específica, registrar los archivos restantes en commits
   pequeños y revisables. No hacer push ni despliegue público sin autorización.

El inventario anterior de archivos corresponde a la pausa. Al reanudar se agregó
también `tests/unit/core/test_database_initialization.py`; no hay cambios staged.
