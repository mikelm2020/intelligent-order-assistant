# Intelligent Order Assistant

Backend de portafolio para gestión de pedidos y asistencia documental con FastAPI,
PostgreSQL/pgvector y LangGraph. Combina reglas transaccionales de inventario con
RAG y acciones de pedidos que se pausan hasta recibir aprobación de un revisor.

## Qué está implementado

- CRUD de clientes y productos, con validación y restricciones de eliminación.
- Creación transaccional de pedidos, precios calculados con `Decimal` y bloqueos
  de inventario. Confirmación/cancelación únicamente desde `pending`.
- Bloqueo de la orden antes de validar transiciones; bloqueo de productos en un
  orden consistente para reducir deadlocks. Cancelación restituye stock una vez.
- Ingestión de texto, fragmentos de 1000 caracteres con solapamiento de 200,
  embeddings de 1536 dimensiones y búsqueda por distancia coseno.
- RAG con `limit` y umbral configurable; sin contexto relevante no llama al chat.
- Grafo determinístico: router → RAG o consulta de pedido → aprobación → acción.
- `interrupt()`/`Command(resume=...)` con el checkpointer oficial de PostgreSQL.
  Las solicitudes sobreviven a nuevas instancias del servicio y conexiones.
- Vista previa, rechazo, caducidad, invalidación por cambios en la orden y recibo
  persistido de ejecución. Repetir la misma decisión devuelve el resultado previo.
- Bearer credentials con roles separados de operador y revisor; API protegida.
- Modo demo offline, pruebas unitarias/integración/evaluación, migraciones,
  workflow de CI y Docker con usuario sin privilegios.

## Arquitectura

```text
FastAPI → servicios → repositorios → SQLAlchemy async → PostgreSQL + pgvector
   ↓          ↓
LangGraph   proveedores de embeddings/chat (OpenAI o demo)
   ↓
pausa persistente → decisión del revisor → OrderService → resultado auditable
```

| Directorio | Responsabilidad |
| --- | --- |
| `app/api/` | HTTP, dependencias y traducción de errores |
| `app/services/` | Negocio, transacciones y coordinación del asistente |
| `app/repositories/` | Consultas y persistencia |
| `app/models/`, `app/schemas/` | Entidades SQLAlchemy y contratos Pydantic |
| `app/graph/` | Estado, routing, consulta, pausa y reanudación |
| `app/ai/` | Protocols y proveedores intercambiables |
| `alembic/` | Migraciones de negocio |
| `scripts/` | Inicialización explícita y demostración |
| `tests/` | Unitarias, integración y evaluación |

PostgreSQL es suficiente para datos, checkpoints y coordinación entre workers.
Redis y RabbitMQ no se incluyen: no hay un caso que justifique esa infraestructura.

## Configuración y desarrollo local

Requisitos: Python 3.12, Poetry 2.4.1 y Docker con Compose. Para builds de Compose
se recomienda Buildx; `docker build` también funciona con el builder clásico.

```bash
poetry install --no-root
cp .env.example .env
```

Configura `.env` sin publicarlo. Genera por separado dos claves de al menos 32
caracteres y una contraseña hex para Docker; por ejemplo `openssl rand -hex 32`.
La aplicación carga `settings` desde variables de entorno y `.env`, con prioridad
para las variables. No imprime las credenciales.

| Variable | Uso |
| --- | --- |
| `DATABASE_URL` | SQLAlchemy async; en desarrollo apunta a localhost:5435 |
| `OPERATOR_API_KEY` | Credencial del operador |
| `REVIEWER_API_KEY` | Credencial distinta para aprobar/rechazar |
| `AI_PROVIDER` | `demo` (offline) o `openai` |
| `OPENAI_API_KEY` | Necesaria solo para solicitudes reales de IA |
| `OPENAI_EMBEDDING_MODEL`, `OPENAI_CHAT_MODEL` | Modelos configurables |
| `RAG_MAX_DISTANCE` | Distancia máxima aceptada; predeterminado `0.4` |
| `APPROVAL_TTL_SECONDS` | Caducidad de solicitudes; predeterminado `900` |
| `DB_PASSWORD` | Contraseña hex usada por `compose.deploy.yaml` |

```bash
docker compose up -d db postgres_test
# Verifica DATABASE_URL y autoriza los cambios de esquema antes de continuar.
poetry run python -m scripts.initialize_database
poetry run uvicorn app.main:app --reload
```

La inicialización ejecuta Alembic y `AsyncPostgresSaver.setup()`. No hay migraciones
implícitas al iniciar el API ni al atender solicitudes. Desarrollo usa `5435` y
las pruebas `5434`. Nunca ejecutar inicialización contra datos reales sin aprobación.

Swagger: `http://127.0.0.1:8000/docs`. Usa Authorize con la credencial correspondiente.
`GET /health` comprueba que el proceso responde; `GET /ready` comprueba conexión,
esquema de aprobaciones/checkpoints y configuración de credenciales.

## API y autorización

Todas las rutas `/api/v1` requieren `Authorization: Bearer <clave>`.

| Recurso | Operaciones |
| --- | --- |
| `/customers` | POST, GET; GET/PATCH/DELETE por ID |
| `/products` | POST, GET; GET/PATCH/DELETE por ID |
| `/orders` | POST, GET; GET por ID |
| `/orders/{id}/confirm`, `/orders/{id}/cancel` | POST exclusivo de revisor |
| `/documents` | POST con título, contenido y fuente opcional |
| `/documents/search` | POST con `query` y `limit` (1–20) |
| `/assistant/ask` | POST con `question` y `limit` (1–20) |
| `/assistant/runs/{id}` | GET de vista previa y resultado |
| `/assistant/runs/{id}/decision` | POST exclusivo de revisor, `{"approve": true/false}` |

Los POST directos de confirmación/cancelación son comandos explícitos de un
revisor y mantienen 409 ante transiciones repetidas o inválidas. El asistente
siempre usa el flujo de pausa y decisión; detectar una intención nunca escribe.

Ejemplo de solicitud con la credencial del operador:

```json
{"question": "Cancelar la orden 15", "limit": 5}
```

La respuesta incluye `status: pending_approval`, `run_id` y `approval` con acción,
ID, estado, total y versión temporal de la orden. La orden sigue sin cambios.
Un revisor inspecciona esa vista previa y envía la decisión usando otra credencial.
El solicitante no puede aprobar su propia solicitud. La decisión no puede cambiar
el ID ni la acción. Un pedido modificado requiere una nueva solicitud.

Las reanudaciones se serializan con un advisory lock de PostgreSQL. El cambio de
pedido y el recibo de ejecución se confirman en la misma transacción, por lo que
un reintento después de perder la respuesta no vuelve a aplicar el inventario.
La aprobación caduca y un cambio posterior de decisión devuelve 409.

## Demostración sin costes externos

Con `AI_PROVIDER=demo`, se usan vectores determinísticos por tema y el chat devuelve
el contexto. **Este modo demuestra el flujo, no calidad semántica ni generación
con un LLM.** No mezcles sus documentos con embeddings reales: usa una base
separada o reingesta el corpus al cambiar de proveedor.

```bash
# Solo en una instancia local de demostración; crea registros sintéticos.
poetry run python -m scripts.demo --prepare --allow-writes
# Revisa la vista previa y decide en un paso separado.
poetry run python -m scripts.demo --approve RUN_ID --allow-writes
# Alternativa: --reject RUN_ID
```

La preparación muestra recuperación documental, fallback, consulta del pedido y
una solicitud pendiente. No confirma ni cancela automáticamente. Las credenciales
se leen de la configuración y no se incluyen en la salida.

## Pruebas y calidad

```bash
poetry run ruff check --no-cache .
poetry run ruff format --check --no-cache .
poetry run pytest tests/unit tests/test_health.py -q
poetry run pytest -q
```

Las unitarias no inicializan la base de datos. Integración y evaluación reutilizan
`session`/`client` de `tests/conftest.py`. Antes de operaciones destructivas se valida
la URL y `current_database()`: solo se admite localhost/127.0.0.1, puerto `5434` y
base `intelligent_order_assistant_test`. `TEST_DATABASE_URL` puede configurar esa
conexión, pero no permite destinos distintos. Se recrean tablas entre casos.

Para una base de testing nueva:

```bash
poetry run python -m scripts.prepare_test_database
```

Este comando verifica testing antes de crear la extensión vector. La suite
incluye un upgrade/downgrade/upgrade real de Alembic en testing, además de pruebas
de RAG, seguridad, aprobación/rechazo, caducidad, replay y carreras de inventario.
Los proveedores OpenAI se simulan; no se hacen llamadas reales ni se usan claves
reales. La evaluación de retrieval usa cinco casos y vectores sintéticos: no
representa una evaluación de calidad de embeddings o respuestas de OpenAI.

CI (`.github/workflows/ci.yml`) define lint, formato, suite y build Docker con una
base PostgreSQL/pgvector efímera. Su ejecución remota requiere publicar la rama;
la existencia del workflow no implica que GitHub Actions ya se haya ejecutado.

## Despliegue Docker reproducible

La imagen usa Python fijado por digest, Poetry fijado y `poetry.lock`. PostgreSQL
17/pgvector está fijado por digest en el Compose de despliegue y en CI. Solo instala
dependencias de producción y no copia `.env`, credenciales ni caches.

Usa un nombre de proyecto separado para no reemplazar los servicios de desarrollo:

```bash
docker build -t intelligent-order-assistant:local .
# Revisa .env, destino y autorización: el servicio migrate modifica el esquema.
docker compose -p ioa-demo -f compose.deploy.yaml up -d
```

El stack crea PostgreSQL, espera su healthcheck, ejecuta la inicialización y luego
arranca el API. El puerto se publica únicamente en localhost. La API corre con
filesystem de solo lectura y sin capabilities; PostgreSQL conserva sus datos en
un volumen. El servicio `migrate` es explícito y no se debe ejecutar simultáneamente
por varios despliegues. En una actualización, reconstruye y recrea los servicios
para ejecutar las migraciones correspondientes antes de arrancar la nueva API.

Detener sin borrar datos:

```bash
docker compose -p ioa-demo -f compose.deploy.yaml down
```

Para exposición pública, coloca un proxy TLS delante del API, restringe la red,
usa un gestor de secretos y configura backups de PostgreSQL. No hay despliegue
cloud ni publicación automática. Las actualizaciones de las imágenes fijadas
requieren revisar el nuevo digest y repetir las verificaciones correspondientes.

### Validar el stack completo con datos de testing

`compose.testing.yaml` se combina exclusivamente con `compose.deploy.yaml` y
un nombre de proyecto separado. Fuerza `AI_PROVIDER=demo`, borra la clave OpenAI,
usa la base `intelligent_order_assistant_test` en almacenamiento efímero y publica
solo el API en `127.0.0.1:19841`. PostgreSQL no tiene puerto publicado ni volumen
persistente. La suite pytest sigue usando su base independiente en `5434`.
El override se verificó con Docker Compose 5.1.4; requiere soporte para las
etiquetas de merge `!reset` y `!override`.

En una misma sesión de shell, genera credenciales exclusivas para esta validación:

```bash
export DB_PASSWORD="$(openssl rand -hex 32)"
export OPERATOR_API_KEY="$(openssl rand -hex 32)"
export REVIEWER_API_KEY="$(openssl rand -hex 32)"
export TEST_IMAGE=intelligent-order-assistant:testing
docker build -t "$TEST_IMAGE" .
docker compose --env-file /dev/null -p ioa-testing -f compose.deploy.yaml -f compose.testing.yaml config --quiet
docker compose --env-file /dev/null -p ioa-testing -f compose.deploy.yaml -f compose.testing.yaml up -d --wait db
docker compose --env-file /dev/null -p ioa-testing -f compose.deploy.yaml -f compose.testing.yaml exec -T db psql -U postgres -d intelligent_order_assistant_test -Atc 'SELECT current_database();'
# Continúa solo si devuelve intelligent_order_assistant_test.
docker compose --env-file /dev/null -p ioa-testing -f compose.deploy.yaml -f compose.testing.yaml up -d --no-build
docker compose --env-file /dev/null -p ioa-testing -f compose.deploy.yaml -f compose.testing.yaml exec -T api python -m scripts.demo --prepare --allow-writes
```

Revisa la vista previa antes de aprobar o rechazar. Ejecuta el script de decisión
en el contenedor `api`, en un paso separado. Reiniciar únicamente `api` permite
comprobar que la solicitud persiste. Reiniciar o retirar `db` pierde los datos
de testing, incluidos los checkpoints. Para terminar y retirar este stack:

```bash
docker compose --env-file /dev/null -p ioa-testing -f compose.deploy.yaml -f compose.testing.yaml down
unset DB_PASSWORD OPERATOR_API_KEY REVIEWER_API_KEY TEST_IMAGE
```

## Límites y trabajo futuro

- Autenticación de servicio single-tenant con dos roles compartidos; no es un
  sistema de usuarios, OAuth ni aislamiento por cliente. La auditoría registra
  roles, decisiones y solicitudes, no identidades personales.
- Routing determinístico en español con infinitivos `confirmar`/`cancelar` y
  referencias `orden/pedido N`. Ambigüedades y negaciones solicitan aclaración.
- RAG concatena fragmentos y usa instrucciones de fundamentación; no verifica
  automáticamente afirmaciones ni devuelve citas estructuradas.
- No hay reranking, evaluación con modelos reales, importación de PDF, índice
  ANN, rate limiting ni paginación. Crear pedidos no tiene Idempotency-Key;
  la garantía de replay descrita corresponde a las decisiones del asistente.
- Los checkpoints se conservan; una política de retención y backups debe definirse
  antes de operar con datos reales a largo plazo.
- Las llamadas OpenAI reales, el CI remoto y un despliegue público se verifican
  por separado; no se presentan como completados sin evidencia.

Consulta `docs/implementation-plan.md` para las fases y la evidencia local.

## Autor

Miguel Angel López Monroy — Backend Python Developer

- [GitHub](https://github.com/mikelm2020)
- [LinkedIn](https://www.linkedin.com/in/miguellopezmdev/)
