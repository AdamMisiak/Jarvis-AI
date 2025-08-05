# Jarvis AI - Personal AI Agent

Peronal AI Agent called Jarvis.

## 🚀 Quick Start

### Prerequisites

- Docker & Docker Compose
- Git

### Installation

1. **Clone and navigate to project**:
```bash
git clone <your-repo>
cd Jarvis-AI
```

2. **Set up environment variables**:
```bash
cp .env.example .env
# Edit .env with your settings
```

3. **Start all services**:
```bash
docker-compose up -d
```

4. **Verify services are running**:
```bash
docker-compose ps
```

The API docs will be available at:
- **Interactive docs**: `http://localhost:8000/docs`

### Health Check

**GET** `/api/health`

```bash
curl "http://localhost:8000/api/health"
```

## ⚙️ Configuration

Environment variables (`.env`):

```env
# Database
POSTGRES_HOST=postgres
POSTGRES_PORT=5432
POSTGRES_USER=jarvis-ai
POSTGRES_PASSWORD=arvis-ai
POSTGRES_DB=arvis-ai

# Redis
REDIS_URL=redis://redis:6379/0

# Server
HOST=0.0.0.0
PORT=8000
DEBUG=false

# Agent
MAX_RESPONSE_LENGTH=1000

# Security
SECRET_KEY=your-super-secret-key-change-in-production

# External APIs
OPENAI_API_KEY=your-openai-key
ANTHROPIC_API_KEY=your-anthropic-key
```

## 🧪 Development

### Local Setup with UV

```bash
# Install UV package manager
pip install uv

# Install dependencies 
uv sync

```

### Database Migrations

```bash
# Generate migration
docker-compose exec api alembic revision --autogenerate -m "description"

# Apply migrations
docker-compose exec api alembic upgrade head
```

## 📦 UV Dependency Management

### Basic Commands

```bash
# Install UV
pip install uv

# Sync dependencies (install from pyproject.toml)
uv sync

# Sync only production dependencies 
uv sync --no-dev

# Update all dependencies to latest versions
uv sync --upgrade
```

### Adding Dependencies

```bash
# Add production dependency
uv add fastapi

# Add dev dependency
uv add --dev pytest
```

### Removing Dependencies

```bash
# Remove dependency
uv remove requests

# Remove dev dependency  
uv remove --dev black
```

### Dependency Information

```bash
# Show dependency tree
uv tree

# List installed packages
uv pip list
```

### Lock Files & Reproducible Builds

```bash
# Generate lock file (uv.lock)
uv lock

# Install from lock file
uv sync --locked

# Update lock file
uv lock --upgrade
```
