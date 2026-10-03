# Intelligent Order Assistant

AI-ready backend for intelligent e-commerce order management, built with FastAPI, PostgreSQL, SQLAlchemy and OpenAI.

The project combines a transactional order-management API with a Retrieval-Augmented Generation (RAG) pipeline capable of ingesting documentation, generating embeddings, performing semantic search with pgvector, and answering questions using only relevant retrieved context.

## Features

### Order Management

- Customer CRUD operations.
- Product CRUD operations.
- Transactional order creation.
- Inventory validation and stock management.
- Row-level locking to protect inventory during concurrent operations.
- Server-side price and order total calculation.
- Order confirmation and cancellation workflows.
- Automatic stock restoration when an order is cancelled.
- Business rules preventing invalid deletions and order transitions.
- Centralized domain error handling.

### AI & RAG

- Document ingestion and automatic chunking.
- OpenAI embeddings.
- Vector storage with PostgreSQL + pgvector.
- Semantic document search using cosine distance.
- Configurable relevance threshold.
- Retrieval-Augmented Generation pipeline.
- OpenAI-powered answers grounded in retrieved documentation.
- Safe fallback when no sufficiently relevant context is found.
- Chat model is not called when retrieval does not meet the relevance threshold.
- Provider abstractions for embedding and chat implementations.

### Quality

- Async application architecture.
- Repository and service layers.
- Alembic database migrations.
- Separate development and test databases.
- Unit tests.
- Integration tests.
- RAG retrieval evaluation tests.
- **87 automated tests currently passing.**

## Architecture

The application follows a layered architecture that separates HTTP concerns, business logic, persistence and AI providers.

```text
Client
  |
  v
FastAPI Routers
  |
  v
Services
  |
  +--------------------+
  |                    |
  v                    v
Repositories       AI Providers
  |               /            \
  v              v              v
PostgreSQL    Embeddings       Chat
+ pgvector      OpenAI         OpenAI
```

Main responsibilities:

- **API layer** — HTTP endpoints, request/response schemas and error translation.
- **Service layer** — business rules, transactional workflows, document ingestion, retrieval and RAG orchestration.
- **Repository layer** — database access and persistence.
- **AI provider layer** — abstractions for embedding and chat providers.
- **PostgreSQL + pgvector** — transactional data and vector similarity search.

## Tech Stack

- Python 3.12+
- FastAPI
- Uvicorn
- SQLAlchemy 2.x (async)
- asyncpg
- PostgreSQL
- pgvector
- Alembic
- Pydantic Settings
- OpenAI API
- Docker Compose
- Poetry
- pytest
- pytest-asyncio
- Ruff

## RAG Pipeline

The assistant uses a Retrieval-Augmented Generation workflow:

```text
Document
   |
   v
Chunking
   |
   v
OpenAI Embeddings
   |
   v
PostgreSQL + pgvector
   |
   v
Semantic Retrieval
   |
   v
Relevance Filtering
   |
   +---- no relevant context ----> Safe fallback
   |
   v
OpenAI Chat Model
   |
   v
Grounded Answer
```

Documents are split into chunks and converted into embeddings using the configured OpenAI embedding model.

When a user asks a question:

1. The question is converted into an embedding.
2. pgvector performs semantic similarity search.
3. Retrieved chunks are filtered using a cosine-distance relevance threshold.
4. If relevant context exists, it is passed to the chat provider.
5. If no context satisfies the threshold, the application returns a safe fallback without calling the chat model.

The default threshold is:

```env
RAG_MAX_DISTANCE=0.4
```

This value is configurable and was selected based on retrieval evaluation cases included in the test suite. It is a project-specific threshold rather than a universal similarity value.

## Transactional Order Processing

Order creation is handled as a transactional workflow.

The backend is responsible for:

- Validating customers and products.
- Validating requested quantities.
- Locking inventory rows during order creation.
- Checking available stock.
- Deriving product prices on the server.
- Calculating the final order total.
- Decrementing stock atomically.
- Restoring inventory when an order is cancelled.

Inventory locking helps prevent concurrent requests from consuming the same available stock.

## Project Structure

```text
app/
├── ai/              # Embedding and chat provider abstractions
├── api/             # FastAPI routers and HTTP error handling
├── core/            # Configuration and database setup
├── exceptions/      # Domain exceptions
├── models/          # SQLAlchemy models
├── repositories/    # Persistence layer
├── schemas/         # Pydantic schemas
└── services/        # Business logic and RAG orchestration

alembic/
└── versions/        # Database migrations

docker/
└── postgres_test/   # Test database initialization

tests/
├── evaluation/      # RAG retrieval evaluation
├── fakes/           # Test providers
├── integration/     # API, repository and service integration tests
└── unit/            # Unit tests
```

## Requirements

Before running the project, install:

- Python 3.12+
- Poetry
- Docker
- Docker Compose

An OpenAI API key is required for real embedding and chat requests.

## Installation

Clone the repository:

```bash
git clone <repository-url>
cd intelligent-order-assistant
```

Install dependencies:

```bash
poetry install
```

Create the environment file:

```bash
cp .env.example .env
```

Then configure your OpenAI API key in `.env`:

```env
OPENAI_API_KEY=your_openai_api_key
```

The default development configuration is:

```env
APP_NAME=Intelligent Order Assistant
ENVIRONMENT=development

DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5435/intelligent_orders

OPENAI_API_KEY=
OPENAI_EMBEDDING_MODEL=text-embedding-3-small
OPENAI_CHAT_MODEL=gpt-5.6-luna
RAG_MAX_DISTANCE=0.4
```

> Never commit your real `.env` file or API key.

## Database

Start PostgreSQL with pgvector:

```bash
docker compose up -d
```

The development database is exposed on port `5435`.

The isolated test database is exposed on port `5434`.

Apply the database migrations:

```bash
poetry run alembic upgrade head
```

## Running the API

Start the FastAPI development server:

```bash
poetry run uvicorn app.main:app --reload
```

The API will be available at:

```text
http://127.0.0.1:8000
```

Health check:

```text
GET /health
```

Interactive Swagger documentation:

```text
http://127.0.0.1:8000/docs
```

## API Endpoints

All application endpoints use the `/api/v1` prefix.

### Customers

| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/v1/customers` | Create customer |
| GET | `/api/v1/customers` | List customers |
| GET | `/api/v1/customers/{customer_id}` | Get customer |
| PATCH | `/api/v1/customers/{customer_id}` | Update customer |
| DELETE | `/api/v1/customers/{customer_id}` | Delete customer |

### Products

| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/v1/products` | Create product |
| GET | `/api/v1/products` | List products |
| GET | `/api/v1/products/{product_id}` | Get product |
| PATCH | `/api/v1/products/{product_id}` | Update product |
| DELETE | `/api/v1/products/{product_id}` | Delete product |

### Orders

| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/v1/orders` | Create order |
| GET | `/api/v1/orders` | List orders |
| GET | `/api/v1/orders/{order_id}` | Get order |
| POST | `/api/v1/orders/{order_id}/confirm` | Confirm order |
| POST | `/api/v1/orders/{order_id}/cancel` | Cancel order |

### Documents

| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/v1/documents` | Ingest document |
| POST | `/api/v1/documents/search` | Semantic document search |

### AI Assistant

| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/v1/assistant/ask` | Ask a question using the RAG pipeline |

## Testing

The project includes unit, integration and RAG retrieval-evaluation tests.

Run the complete test suite:

```bash
poetry run pytest
```

Current test status:

```text
87 passed
```

The test suite covers:

- Customer and product operations.
- Transactional order workflows.
- Order status transitions.
- Inventory behavior.
- Document ingestion and chunking.
- Vector similarity search.
- Document retrieval.
- RAG relevance filtering.
- OpenAI provider behavior using controlled test doubles.
- RAG fallback behavior.
- Retrieval evaluation metrics.

## RAG Evaluation

Retrieval quality is evaluated separately from the generative model.

The evaluation suite contains controlled questions and expected document matches. This allows retrieval behavior to be validated deterministically and helps tune the relevance threshold without depending on subjective LLM output.

This separation is intentional:

```text
Retrieval quality != Generation quality
```

A RAG system should first retrieve appropriate context before asking a language model to generate an answer.

## Key Technical Decisions

### Async SQLAlchemy

Database access uses SQLAlchemy 2.x with `asyncpg`, keeping the FastAPI request path asynchronous.

### PostgreSQL + pgvector

Transactional application data and vector embeddings are stored within the PostgreSQL ecosystem. pgvector provides semantic similarity search without introducing a separate vector database at this stage of the project.

### Server-Side Business Rules

Prices, totals, stock changes and order transitions are controlled by the backend rather than trusted from client input.

### Inventory Locking

Order creation uses database-level row locking when working with inventory, helping reduce race conditions when concurrent requests attempt to consume the same stock.

### Provider Abstractions

Embedding and chat functionality are accessed through provider abstractions instead of coupling business services directly to OpenAI implementations.

This improves testability and makes it possible to replace provider implementations later.

### Configurable RAG Threshold

The relevance threshold is controlled by server configuration rather than by API clients. This prevents consumers from bypassing the application's relevance policy.

The current default is:

```env
RAG_MAX_DISTANCE=0.4
```

### Safe RAG Fallback

When retrieval cannot find sufficiently relevant documentation, the system returns:

```text
No tengo información suficiente en la documentación disponible para responder esa pregunta.
```

The chat model is not called in this case, avoiding an unnecessary model request when the available documentation cannot support an answer.

## Roadmap

The current version provides the transactional backend and the initial RAG architecture.

Potential next iterations include:

- Richer RAG evaluation metrics.
- Source citations in assistant responses.
- Multi-chunk context strategies.
- LangGraph-based orchestration and routing.
- Tool and action execution.
- Human-in-the-loop workflows.
- Redis and RabbitMQ integrations.
- External automation integrations.
- Cloud deployment.

> These items are roadmap work and are not presented as currently implemented features.

## Project Status

**Version:** 0.1.0

The project is under active development as a backend and applied-AI portfolio project focused on production-oriented engineering practices, transactional consistency, testability and grounded AI responses.

## Author

**Miguel Angel López Monroy**

Backend Python Developer

- GitHub: [mikelm2020](https://github.com/mikelm2020)
- LinkedIn: [miguellopezmdev](https://www.linkedin.com/in/miguellopezmdev/)
