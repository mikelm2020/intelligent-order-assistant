# Estado del desarrollo

Fecha de última actualización: 2026-10-08 (America/Mexico_City).
Rama: `feature/langgraph-orchestration`.
HEAD al comenzar la reanudación: `cfba253` (consultar Git para el HEAD actual).

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
`b60d0bf` (CI), `fb56eab` (documentación).

## Fase 2: suite completa y build actual (2026-10-08)

- Se verificaron la URL efectiva y `current_database()` antes de la suite:
  `localhost:5434/intelligent_order_assistant_test`, PostgreSQL **17.11**.
- `poetry run pytest -q -x --tb=short`, con `TEST_DATABASE_URL` y `DATABASE_URL`
  fijados explícitamente a ese destino: **156 passed en 22.55 s**. Incluye el
  round trip de migraciones y `alembic check`; proveedores de IA simulados.
- `docker build -t intelligent-order-assistant:validation-20261008 .`: correcto,
  imagen `a5a18f53ceb2`. Buildx sigue ausente; el builder clásico completó el build.
- No se afectaron contenedores de desarrollo ni otros proyectos. Suite finalizada
  antes de iniciar la demostración.
- Se prepara `compose.testing.yaml` para verificar el stack completo con una base
  efímera llamada `intelligent_order_assistant_test`, sin volumen persistente y
  sin publicar PostgreSQL. El API usará un puerto dedicado en localhost.

## Fase 3: stack completo y demo offline (2026-10-08)

- Override `compose.testing.yaml`: base efímera `intelligent_order_assistant_test`,
  sin volumen persistente ni puerto PostgreSQL publicado; API en localhost:19841,
  proveedor demo y clave OpenAI vacía. Configuración combinada validada tanto
  por Compose como por assertions de sus propiedades antes de iniciar servicios.
- Proyecto separado `ioa-validation-20261008`, sin afectar los contenedores
  existentes. Se inició primero `db` y se verificó `current_database()` antes
  de ejecutar inicialización. La conexión del stack utiliza su red interna
  `db:5432/intelligent_order_assistant_test`; no se ejecutó pytest en ese destino.
- `up -d --no-build` completó PostgreSQL → inicialización → API. `migrate` terminó
  con exit 0; revisión de solo lectura confirmó revisión Alembic
  `20261007_assistant_runs` y diez migraciones del checkpointer.
- `scripts.demo --prepare --allow-writes`, dentro del API: recuperación de
  devoluciones, fallback sin información, consulta y solicitud pendiente.
- Health/readiness OK, 401 sin credenciales, UID 10001, ausencia de `/app/.env`,
  filesystem de solo lectura, `cap_drop=ALL`, `no-new-privileges=true`.
- Se reinició exclusivamente `api`: healthy; solicitud y vista previa siguen
  persistidas; orden 1 pendiente, total 51.00, stock 8. No hubo cancelación.
- Revisión automática rechazó `scripts.demo --approve` para esa orden sintética:
  requiere autorización de la acción concreta además de la autorización general
  de integración. No se intentó ejecutarla indirectamente ni por otra vía.
- Acción pendiente: cancelar orden sintética 1, solicitud
  `2afffa8f-b620-4b49-a4d3-6442b6debdde`, exclusivamente en el stack efímero.
  La decisión y su replay actuales no se presentan como comprobados. Los tests
  automatizados de aprobación/replay sí forman parte de la suite de 156 casos.
- El stack efímero permanece activo para permitir esa decisión. Configuración
  temporal con claves exclusivas de testing en un archivo de permisos 0600 bajo
  `/tmp/ioa-validation-20261008-gloatt4_`; nunca incorporada a Git ni mostrada.
- README y plan actualizados con instrucciones reproducibles del stack de testing
  y con la distinción entre evidencia histórica, suite actual y decisión pendiente.
- Cierre de fase: Ruff check y formato conformes (117 archivos),
  `git diff --check` sin errores. Solo configuración/documentación cambió después
  de la suite; no se repitieron tests sin nuevos cambios de Python.

## Cierre solicitado de la fase 5: caducidad y limpieza (2026-10-08)

- El usuario autorizó expresamente cancelar la orden sintética 1 mediante la
  solicitud `2afffa8f-b620-4b49-a4d3-6442b6debdde`, solo en
  `ioa-validation-20261008`, y retirar después los recursos de esa demo.
- Se verificaron etiquetas Docker del proyecto, contenedores activos,
  `current_database() = intelligent_order_assistant_test`, configuración efectiva
  `ENVIRONMENT=testing`, proveedor demo y conexión interna `db:5432` a esa base.
- Consulta HTTP autenticada como revisor: ID exacto, acción cancel, orden 1,
  total 51.00; la orden seguía pending y el stock era 8. La solicitud devolvió
  **expired**, por lo que no era válida para aprobación HITL.
- No se envió la decisión, no se alteró TTL/fecha/estado y no se generó otra
  solicitud. La autorización exacta no se amplió a una solicitud nueva.
- La cancelación, stock final 10 y replay de esta demo no se verificaron.
  Las pruebas automatizadas de esos comportamientos sí pasaron en la suite
  previa de 156 casos. No presentar la demo expirada como una cancelación exitosa.
- Limpieza autorizada completada: `docker compose ... down` del proyecto exacto,
  retirada de la etiqueta `intelligent-order-assistant:validation-20261008` y
  eliminación exclusiva del archivo `testing.env` y su directorio temporal.
  No se usó prune, no había volumen persistente, no se eliminaron imágenes base
  ni contenedores de desarrollo/testing existentes u otros proyectos.
- Fases 1–4 del plan implementadas y verificadas localmente. Documentación de
  fase 5 actualizada; cierre de validación HITL bloqueado por la caducidad de la
  solicitud autorizada. No se declaran completas las cinco fases.
- Solo se modificaron documentos; no se introdujeron nuevas funcionalidades.
- Verificaciones finales: Ruff check y formato sin errores (117 archivos),
  `git diff --check` sin errores; consultas Docker por etiqueta de proyecto
  confirmaron ausencia de contenedores/redes/volúmenes de la demo y los servicios
  preexistentes siguen activos. Archivo temporal y etiqueta de imagen retirados.
  No se repitió pytest ni build: no cambió Python ni configuración desde las
  verificaciones previas de 156 casos y build exitoso. Se registra este cierre
  en un commit local de documentación; no se hizo push.

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
  registrados en commits locales. La documentación de la nueva validación se
  registra al cerrar esta fase.
- PostgreSQL 17 está fijado en despliegue/CI con el digest verificado localmente:
  `pgvector/pgvector@sha256:cf134a767f474095eeba57e0117be8e568e011a63f33fbf252f14c9b760f8e6f`.
  Python también está fijado por digest en Dockerfile.
- Stack completo verificado con el override efímero de testing. El Compose de
  despliegue con datos persistentes de desarrollo/producción no se ejecutó.
- La solicitud anterior expiró y no se ejecutó. La nueva demo HITL ya completó
  aprobación, cancelación y replay con autorización específica; ambas demos
  temporales fueron retiradas. Las cinco fases del plan están completas localmente.
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

Los commits posteriores a la pausa se realizaron al recibir la autorización
de reanudación: `d5b71ac`, `7428837`, `b60d0bf`, `fb56eab`, `391584c`, `fe51ee8`.

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

## Próximos pasos

### Revisión del README previa a publicación (2026-10-08)

- README reescrito en español tras contrastar routers, schemas, servicios,
  grafo, seguridad, configuración, scripts, Docker/Compose y CI con el código.
- Incluye problema, características reales, diagrama Mermaid, flujos RAG/HITL,
  tecnologías, instalación, configuración, endpoints y ejemplos HTTP, demo,
  testing y límites. Distingue búsqueda sin umbral de RAG y roles de identidades.
- Validación documental: 20 bloques Bash con `bash -n`, contratos JSON con
  Pydantic, rutas/métodos contra OpenAPI, rutas de salud/documentación y enlaces
  locales. Compose validado con variables ficticias; Ruff y formato correctos.
- Sin llamadas HTTP reales, conexiones a bases, inicialización, tests destructivos
  ni costes de IA. No se repitió la suite ni el build por un cambio documental.
- Cambian únicamente README y este registro. Commit local autorizado, sin push
  ni PR; publicación pendiente de revisión del usuario.

### Nueva demo HITL completada y fase 5 cerrada (2026-10-08)

- Proyecto Docker nuevo: `ioa-hitl-final-20261008`, base efímera exclusiva
  `intelligent_order_assistant_test`, conexión interna `db:5432`, API localhost:19841.
- Destino verificado mediante `current_database()` antes de inicialización y
  configuración efectiva del API comprobada: testing, demo offline y
  `APPROVAL_TTL_SECONDS=86400` (24 horas), sin alterar validaciones de aprobación.
- Imagen construida desde el código actual: `intelligent-order-assistant:hitl-final-20261008`,
  ID `c8cdec89fa02`. Preparación de demo completada con RAG/fallback/consulta/pausa.
- Nueva solicitud: `6f345657-4980-4be5-9f44-b1810886fd31`; cancelar orden sintética 1,
  total 51.00. El usuario aprobó expresamente esta solicitud concreta.
- Antes de ejecutar se verificaron etiquetas del proyecto, `current_database()`,
  conexión efectiva del API, testing/demo, solicitud vigente pending_approval,
  acción cancel, orden 1 pendiente y stock inicial 8. No se reutilizó la anterior.
- Decisión por HTTP con credencial revisor: resultado **completed**, orden
  **cancelled**, stock **10**. Repetir la misma decisión devolvió un resultado
  idéntico, orden cancelada y stock **10**, sin doble restitución.
- Retirados solo los tres contenedores y red de `ioa-hitl-final-20261008`, la
  etiqueta de imagen de esta demo y el archivo de credenciales/directorio temporal.
- Las cinco fases del plan están completas dentro del alcance local. La caducidad
  del intento anterior se conserva como evidencia histórica, no como pendiente.
- Se actualiza únicamente documentación; no se agregaron funcionalidades ni se
  cambió Python. No corresponde repetir suite/build por esos cambios documentales.
- Verificación final: Ruff check correcto, formato conforme (117 archivos),
  `git diff --check` sin errores. Consultas Docker por etiqueta confirmaron que
  no quedan contenedores, redes ni volúmenes del nuevo proyecto; los contenedores
  existentes siguen activos. Última suite completa: **156 passed en 22.55 s**.
  Preparación y aprobación/replay de la nueva demo completadas con assertions reales.

1. Para GitHub: `origin` está configurado y la rama local no tiene upstream.
   Pendiente autorización separada de push, ejecución/revisión de CI remoto y PR
   contra `main`. No se hicieron operaciones remotas de escritura.
2. Llamadas OpenAI y despliegue público permanecen fuera del alcance.

El inventario anterior de archivos corresponde a la pausa y es histórico.
