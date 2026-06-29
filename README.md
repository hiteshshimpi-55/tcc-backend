# TCC Backend

Production-grade FastAPI starter for building agentic AI systems with LangGraph, LangSmith tracing, PostgreSQL checkpoint persistence, and standardized API responses.

## Features

- **FastAPI** with app factory pattern and lifespan management
- **LangGraph** ReAct agent with tool calling and PostgreSQL checkpoint persistence
- **LangSmith** tracing via environment variables
- **Standardized API envelope** for all success and error responses
- **Global exception handlers** with production-safe error messages
- **Request ID** propagation (`X-Request-ID`) and structured JSON logging
- **Health checks** — liveness and readiness (Postgres)
- **SSE streaming** for agent responses
- **Optional API key** authentication on agent routes
- **Pre-commit hooks** — Ruff lint/format, file hygiene, pytest on push
- **GitHub Actions CI** — lint, format check, and tests on every PR

## Quick Start

### Prerequisites

- Python 3.11+
- [uv](https://docs.astral.sh/uv/)
- Docker (for PostgreSQL)

### Setup

```bash
# Install dependencies (uses Python version from .python-version)
make setup

# Or step by step:
uv sync --all-extras
make install-hooks

# Configure environment
cp .env.example .env
# Edit .env with your OPENAI_API_KEY and other settings

# Start PostgreSQL
docker compose up -d postgres

# Run the API (development with hot reload)
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

API docs: http://localhost:8000/docs

### Run with Docker (full stack)

```bash
docker compose up --build
```

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/health/live` | GET | Liveness probe |
| `/api/v1/health/ready` | GET | Readiness probe (checks Postgres) |
| `/api/v1/agents/invoke` | POST | Run agent on a thread |
| `/api/v1/agents/stream` | POST | Stream agent response (SSE) |

### Example: Invoke Agent

```bash
curl -X POST http://localhost:8000/api/v1/agents/invoke \
  -H "Content-Type: application/json" \
  -d '{"thread_id": "session-1", "message": "What time is it?"}'
```

### Example: Stream Agent

```bash
curl -N -X POST http://localhost:8000/api/v1/agents/stream \
  -H "Content-Type: application/json" \
  -d '{"thread_id": "session-1", "message": "Calculate 15 * 7"}'
```

## Response Format

All responses use a consistent envelope:

**Success:**
```json
{
  "success": true,
  "data": { ... },
  "meta": {
    "request_id": "uuid",
    "timestamp": "2026-06-28T12:00:00Z"
  }
}
```

**Error:**
```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Request validation failed",
    "details": [{ "field": "body.message", "message": "Field required" }]
  },
  "meta": {
    "request_id": "uuid",
    "timestamp": "2026-06-28T12:00:00Z"
  }
}
```

## LangSmith Tracing

Set these in `.env` to enable tracing:

```
LANGCHAIN_TRACING_V2=true
LANGCHAIN_API_KEY=lsv2_...
LANGCHAIN_PROJECT=tcc-backend
```

## Development

### Pre-commit

Hooks run automatically on `git commit` (lint/format/hygiene) and `git push` (pytest).

```bash
make install-hooks   # one-time setup (commit + push hooks)
make pre-commit      # run all hooks manually
make reset-env       # recreate .venv if uv run/pytest/pre-commit fail after moving the repo
make lint            # ruff check only
make format          # ruff format + auto-fix
make check           # lint + format check + pytest
```

### Testing

```bash
make test
make test-cov
# or
uv run pytest
uv run pytest --cov=app
```

## Project Structure

```
app/
├── main.py              # FastAPI app factory
├── config.py            # Pydantic settings
├── lifespan.py          # Startup/shutdown (checkpointer)
├── logging.py           # structlog configuration
├── middleware/          # Request ID, logging
├── api/                 # Routes and dependencies
├── core/                # Exceptions and handlers
├── schemas/             # Request/response models
├── agents/              # LangGraph agent, tools, checkpointer
└── services/            # Business logic layer
```

## Environment Variables

See [`.env.example`](.env.example) for all configuration options.
