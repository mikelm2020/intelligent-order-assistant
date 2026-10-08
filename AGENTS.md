# Guía de trabajo para agentes

## Proyecto y arquitectura

Intelligent Order Assistant es un backend asíncrono con FastAPI, SQLAlchemy,
PostgreSQL y pgvector para gestionar pedidos y responder preguntas mediante RAG.
Utiliza Poetry y Python compatible con `^3.12`.

La aplicación utiliza `settings`, cargado desde variables de entorno y `.env`.
Verificar el destino efectivo antes de ejecutar cualquier comando que acceda a
bases de datos; no asumir que corresponde a desarrollo o testing por el nombre
del comando.

Mantener la separación de responsabilidades:

- `app/api/`: endpoints HTTP, dependencias y traducción de errores.
- `app/services/`: reglas de negocio, transacciones, ingestión, recuperación y RAG.
- `app/repositories/`: acceso a datos y consultas SQLAlchemy.
- `app/models/`: entidades, relaciones y restricciones de persistencia.
- `app/schemas/`: validación y contratos de entrada y salida con Pydantic.
- `app/ai/`: interfaces, factories y proveedores de embeddings y chat.
- `app/graph/`: estado, nodos y orquestación con LangGraph.
- `app/core/`: configuración y sesiones de base de datos.
- `alembic/`: migraciones; `tests/`: pruebas unitarias, integración y evaluación.

Reutilizar los servicios existentes desde la API y LangGraph. No duplicar reglas
de negocio en nodos o routers ni acoplar servicios directamente a proveedores
externos. Evitar dependencias nuevas si las herramientas existentes son suficientes.

Actualmente `/api/v1/assistant/ask` ejecuta RAG directamente. El grafo tiene rutas
de conocimiento y consulta de pedidos, pero no está integrado en ese endpoint.
La declaración de `order_action` no implica que existan acciones implementadas.

## Pedidos y escrituras de negocio

- Utilizar `Decimal` para dinero; calcular precios, subtotales y totales en el
  backend, sin confiar en importes enviados por clientes.
- Preservar transacciones, bloqueos de inventario, rollback y transiciones válidas
  de `pending` a `confirmed` o `cancelled`, incluida la restitución de stock.
- Considerar concurrencia e idempotencia en creación y transiciones. Revisar
  carreras entre confirmación y cancelación y evitar restituciones duplicadas.
- No ejecutar escrituras de negocio sin autorización explícita.
- No ejecutar confirmaciones ni cancelaciones desde el asistente sin autorización
  explícita y aprobación de la acción concreta. Detectar una intención o un ID no
  constituye aprobación. Los flujos deben permitir revisar la acción antes de
  ejecutarla y reutilizar `OrderService`.

Estas reglas de aprobación son instrucciones para agentes y requisitos de
funcionalidades futuras. Los endpoints actuales de pedidos no implementan
autenticación ni aprobación humana. No presentar esas protecciones como
funcionalidades ya implementadas.

## RAG y LangGraph

- Preservar el umbral configurable `rag_max_distance` (`RAG_MAX_DISTANCE`, valor
  predeterminado `0.4`) y su control desde el servidor.
- Si no hay fragmentos suficientemente relevantes, mantener el fallback de
  información insuficiente sin llamar al proveedor de chat.
- Mantener compatibilidad con embeddings de 1536 dimensiones en pgvector. Un
  cambio de modelo o dimensiones exige revisar persistencia y migraciones.
- Preservar y propagar `limit` y `max_distance` entre API, grafo y servicios.
  El `RAGNode` actual no los propaga: atender esta limitación al integrar el grafo.
- Mantener proveedores intercambiables y comprobables mediante sus interfaces.

## Pruebas y calidad

- Agregar o actualizar pruebas enfocadas para cambios de comportamiento y
  correcciones, incluyendo casos de error y concurrencia cuando correspondan.
- Usar mocks, fakes y overrides de dependencias para IA; no llamar a OpenAI real
  en pruebas automatizadas ni generar costes sin autorización explícita.
- Ejecutar Ruff y las pruebas enfocadas apropiadas cuando el alcance autorizado
  lo permita. No ejecutar comprobaciones que el usuario haya prohibido.
- Los nuevos tests de integración deben reutilizar las fixtures `session` y
  `client` de `tests/conftest.py`, según corresponda. No utilizar directamente
  el engine ni la fábrica de sesiones de la aplicación.
- Antes de ejecutar pruebas que invoquen `drop_all` o `create_all`, verificar la
  conexión efectiva y confirmar que apunta
  exclusivamente a testing: base `intelligent_order_assistant_test`, puerto local
  `5434`, nunca a desarrollo o producción.
- `tests/conftest.py` tiene una fixture global `autouse` que ejecuta `drop_all`
  y `create_all` antes de cada test y `drop_all` después, incluso en unitarios.
  Una ejecución enfocada también requiere verificar el destino y autorización
  para esas operaciones destructivas; no asumir que es inocua por ser unitaria.
- Una autorización previa que cubra la ejecución de las pruebas y sus efectos
  destructivos es suficiente; no solicitarla repetidamente. La verificación del
  destino efectivo sigue siendo obligatoria.
- Los tests crean tablas desde metadata: su éxito no valida las migraciones.
- Reportar comandos ejecutados, resultados reales y verificaciones omitidas.
  No presentar cifras del README o una inspección estática como pruebas pasadas.

## Comandos del repositorio

Ejecutar desde la raíz. Esta lista documenta comandos; no autoriza su ejecución.

| Propósito | Comando | Condición |
| --- | --- | --- |
| Instalar dependencias | `poetry install` | Solo dentro del alcance autorizado. |
| Levantar bases de datos | `docker compose up -d db postgres_test` | Requiere autorización para iniciar servicios. |
| Iniciar API local | `poetry run uvicorn app.main:app --reload` | Usa `settings`, cargado desde variables de entorno y `.env`; verificar el destino efectivo. |
| Revisar lint | `poetry run ruff check --no-cache .` | Sin correcciones automáticas. |
| Comprobar formato | `poetry run ruff format --check --no-cache .` | Sin modificar archivos. |
| Pruebas de nodos | `poetry run pytest tests/unit/graph/test_nodes.py` | Verificar testing y autorizar efectos destructivos de la fixture. |
| Pruebas del grafo | `poetry run pytest tests/unit/graph/test_graph.py` | Mismas condiciones para la base de pruebas. |
| Pruebas RAG | `poetry run pytest tests/unit/services/test_rag.py tests/integration/api/test_assistant_rag.py` | Mismas condiciones para la base de pruebas. |
| Suite completa | `poetry run pytest` | Mismas condiciones para la base de pruebas. |
| Aplicar migraciones | `poetry run alembic upgrade head` | Solo con autorización explícita y destino verificado. |
| Inspeccionar Git | `git status --short --branch` y `git diff` | Operaciones de lectura. |

Compose expone desarrollo en `5435` y testing en `5434`. Alembic obtiene el
destino de `settings.database_url`; no asumir que apunta a testing.

## Git y autorización

- Inspeccionar el estado de Git antes de editar y preservar cambios existentes
  del usuario, aunque estén incompletos o fuera del alcance de la tarea.
- No revertir, sobrescribir ni incorporar cambios ajenos sin autorización.
- Utilizar Conventional Commits y commits pequeños, coherentes y revisables
  cuando el usuario autorice realizarlos.
- Solicitar autorización antes de commit, push, ejecución de migraciones o
  acciones destructivas. La autorización debe cubrir la acción concreta.
- Respetar las restricciones del usuario sobre archivos y comandos; no ampliar
  el alcance bajo el pretexto de completar verificaciones o mejoras.

## Seguridad

No exponer ni registrar claves API, credenciales o contenido secreto de `.env`.
No incluir secretos en código, documentación, pruebas, commits o respuestas.
Usar configuración y ejemplos sin credenciales reales. Las herramientas de IA
no deben omitir las reglas de negocio, autorización o aprobación de escrituras.

## Documentación

Mantener el README actualizado cuando cambien comportamiento, API, arquitectura
o comandos, siempre dentro del alcance autorizado. Si no se permite editarlo,
reportar la actualización pendiente.

Distinguir claramente lo implementado en código, lo probado con resultados
verificados y lo pendiente. No presentar roadmap como funcionalidad disponible
ni afirmar integración HTTP de LangGraph mientras no exista.

## Metodología

Inspeccionar código, pruebas y estado de Git antes de actuar. Trabajar en
incrementos pequeños orientados a corrección y mantenibilidad; reutilizar
patrones existentes, verificar lo cambiado y comunicar limitaciones reales.
Evitar refactors, dependencias, funcionalidades o cambios de archivos ajenos a
la solicitud. Ante una ambigüedad que afecte autorización o escrituras de negocio,
aclararla antes de ejecutar la acción dependiente.
