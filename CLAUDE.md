# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Jarvis-AI is a personal AI agent built with FastAPI that provides an intelligent chat interface with integrated web search capabilities, LLM integration (OpenAI GPT-4o), and observability via Langfuse tracing.

## Development Commands

### Local Development (UV Package Manager)
```bash
# Install dependencies
uv sync

# Install production dependencies only
uv sync --no-dev

# Add dependencies
uv add <package>          # production
uv add --dev <package>    # development

# Run the application locally
python -m app.main
# Or with uvicorn directly:
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### Docker Development
```bash
# Start all services (Postgres, Redis, API)
docker-compose up -d

# Stop services
docker-compose down

# View logs
docker-compose logs -f api

# Rebuild after changes
docker-compose up -d --build
```

### Database Migrations
```bash
# Generate new migration
docker-compose exec api alembic revision --autogenerate -m "description"

# Apply migrations
docker-compose exec api alembic upgrade head

# Rollback migration
docker-compose exec api alembic downgrade -1
```

### Code Quality
```bash
# Format code
black app/

# Sort imports
isort app/

# Type checking
mypy app/
```

## Architecture

### Core Service Layer (app/services/)

The application uses a service-oriented architecture with three main services:

1. **AssistanceService** (`assistance_service.py`): Main orchestrator
   - Entry point for all chat interactions via `handle_chat_message()`
   - Coordinates between LLMService, WebSearchService, and LangfuseService
   - Manages message persistence to database
   - Decides whether web search is needed based on user query
   - All operations are traced with Langfuse `@observe` decorator

2. **LLMService** (`llm_service.py`): LLM interaction layer
   - Direct HTTP requests to OpenAI API (not using SDK)
   - Uses `BASE_SYSTEM_PROMPT` from `app/prompts/base.py`
   - Default model: GPT-4o (configurable)
   - All requests traced via Langfuse

3. **WebSearchService** (`web_search_service.py`): Intelligent search decisioning
   - `is_web_search_needed()`: Determines if query needs web search (uses GPT-4o-mini)
   - `generate_queries()`: Generates targeted search queries for whitelisted domains
   - Filters queries against `RESOURCES` constant (whitelist of ~50 trusted domains)
   - Returns structured JSON with thoughts and filtered queries

4. **LangfuseService** (`langfuse_service.py`): Observability
   - Provides context managers for tracing (`span()`)
   - Updates traces with metadata, input/output
   - Must call `flush()` in finally blocks

### Data Flow

```
User Request → AssistanceService.handle_chat_message()
    ↓
    1. Save user message to DB (ChatMessage model)
    ↓
    2. Check if web search needed (WebSearchService.is_web_search_needed)
    ↓
    3a. If YES: Generate queries (WebSearchService.generate_queries)
                Filter against RESOURCES whitelist
    ↓
    3b. If NO: Generate AI response (LLMService.generate_response)
    ↓
    4. Save AI response to DB
    ↓
    5. Return ChatResponse with message + metadata
```

### Configuration (app/config/)

- **settings.py**: Pydantic Settings with `.env` file loading
  - Database: Postgres with asyncpg driver
  - Redis: Caching layer (configured but not heavily used yet)
  - External APIs: OpenAI, Anthropic, FireCrawl
  - Langfuse: Tracing configuration
  - All settings loaded via `get_settings()` cached singleton

- **constants.py**: Global constants
  - `RESOURCES`: Whitelist of trusted domains for web search (brain.overment.com, nextjs.org, arxiv.org, etc.)

### Database Models (app/models/)

- **ChatMessage** (`chat_message.py`): Single table for all messages
  - Stores both user and AI messages (distinguished by `is_user_message` boolean)
  - `metadata_json`: Optional JSON field for contextual data
  - Uses async SQLAlchemy with asyncpg

### API Layer (app/api/routes/)

- **chat.py**: Main chat endpoint
  - `POST /api/chat`: Accepts ChatRequest, returns ChatResponse
  - Uses FastAPI dependency injection for AssistanceService
  - Error handling currently commented out for development

- **health.py**: Health check endpoint
  - `GET /api/health`: Basic service health check

### Prompts (app/prompts/)

- **base.py**: Default system prompt for general chat
- **search.py**: Specialized prompts for web search detection and query generation

## Important Implementation Details

### Langfuse Tracing Pattern
All service methods that need tracing use the `@observe()` decorator:
```python
@observe(name="operation_name")
async def method():
    # Automatic trace creation
    pass
```

For manual span management within traced functions:
```python
with self.langfuse_service.span("step_name", input_data={...}):
    result = await operation()
    self.langfuse_service.update_span(output=result)
```

### Async Patterns
- All database operations use async SQLAlchemy with asyncpg
- HTTP requests to LLM APIs use httpx.AsyncClient
- FastAPI routes are async by default

### Error Handling
Currently in development mode with minimal error handling. Production implementation should:
- Catch specific exceptions in chat route
- Return structured ChatError responses
- Log errors to Langfuse with appropriate metadata

## Environment Setup

Required environment variables (see `.env.example`):
- `DATABASE_URL`: Postgres connection string
- `REDIS_URL`: Redis connection string
- `OPENAI_API_KEY`: Required for LLM service
- `LANGFUSE_SECRET_KEY`, `LANGFUSE_PUBLIC_KEY`: Required for tracing
- `FIRECRAWL_API_KEY`: Optional, for web scraping functionality

## Git Commit Conventions

Follow conventional commits with emoji prefixes (see `cursor/rules/commit.mdc`):
- ✨ feat: New features
- 🐛 fix: Bug fixes
- ♻️ refactor: Code restructuring
- 📝 docs: Documentation changes
- ✅ test: Test additions/corrections
- 🧑‍💻 chore: Tooling and configuration

Commit format: `type(scope): description`
Write in imperative mood and explain why, not just what.
