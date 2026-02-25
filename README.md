# Chip Fault AI Agent System

AI-driven chip failure analysis system for self-developed SoC chips, supporting multi-module fault localization, root cause reasoning, and knowledge closed-loop.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.12](https://img.shields.io/badge/python-3.12-blue.svg)](https://www.python.org/downloads/release/python-3120/)
[![Docker](https://img.shields.io/badge/docker-latest-blue.svg)](https://www.docker.com/)

## Features

### Core Capabilities
- **Multi-Source Reasoning**: Knowledge graph + case matching + rule-based inference
- **Log Parsing**: Automatic feature extraction from chip logs
- **Intelligent Reporting**: Auto-generated HTML analysis reports
- **Expert Feedback Loop**: Learn from expert corrections to improve accuracy
- **Multi-Turn Conversation**: Interactive dialog for deeper analysis

### Technical Highlights
- **Local Embedding**: BGE model for Chinese text processing (offline-capable)
- **Multi-Agent Architecture**: Agent1 (reasoning) + Agent2 (expert interaction)
- **RBAC Security**: Role-based access control with JWT authentication
- **Hybrid Storage**: PostgreSQL + pgvector + Neo4j + Redis
- **Docker Deployment**: Complete containerization with offline support
- **System Monitoring**: Real-time health checks and alerting

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        Frontend (React + Vite)                  │
│                    http://localhost:3000                        │
└─────────────────────────────┬───────────────────────────────────┘
                              │
┌─────────────────────────────▼───────────────────────────────────┐
│                      FastAPI Backend (Port 8889)                │
│  ┌───────────────┐  ┌──────────────┐  ┌─────────────────────��  │
│  │   Auth/JWT    │  │  Routes      │  │   Monitoring        │  │
│  │   RBAC        │  │  - Analyze   │  │   Health Checks     │  │
│  │               │  │  - Expert    │  │   Alerts            │  │
│  └───────────────┘  │  - Admin     │  └─────────────────────┘  │
│                     └──────────────┘                            │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                 Multi-Agent Orchestrator                │   │
│  │  ┌────────────┐              ┌────────────┐             │   │
│  │  │  Agent1    │              │  Agent2    │             │   │
│  │  │  Reasoning │◄────────────►│  Expert    │             │   │
│  │  │  Core      │              │  Knowledge │             │   │
│  │  └────────────┘              │  Loop      │             │   │
│  │                              └────────────┘             │   │
│  └─────────────────────────────────────────────────────────┘   │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                    MCP Tools Layer                      │   │
│  │  Log Parser | KG Query | Case Match | Rule Engine      │   │
│  └─────────────────────────────────────────────────────────┘   │
└─────────────────────────────┬───────────────────────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        │                     │                     │
┌───────▼────────┐   ┌────────▼────────┐   ┌───────▼────────┐
│  PostgreSQL    │   │     Neo4j       │   │     Redis      │
│  + pgvector    │   │   Knowledge     │   │    Cache       │
│  (Vector DB)   │   │     Graph       │   │   (Sessions)   │
└────────────────┘   └─────────────────┘   └────────────────┘
```

## Quick Start

### Prerequisites

- **Windows 10/11** or **Linux** (Docker deployment recommended)
- **Docker Desktop** 4.0+ (with WSL 2 on Windows)
- **Python 3.12** (for development)
- **8GB+ RAM** recommended

### Option 1: Docker Deployment (Recommended)

```bash
# Clone the repository
git clone https://github.com/xpengch/chip-fault-agent.git
cd chip-fault-agent

# Copy environment template
cp .env.docker.template .env

# Edit .env and set ANTHROPIC_API_KEY
notepad .env  # Windows
# nano .env   # Linux

# Start all services
docker compose up -d

# View logs
docker compose logs -f
```

**Access URLs:**
- Frontend: http://localhost:3000
- Backend API: http://localhost:8889
- API Documentation: http://localhost:8889/docs

### Option 2: Offline Deployment

For air-gapped environments, use the complete offline package:

```bash
# Run the export script to create offline package
export-offline.bat  # Windows
# or
./export-offline.sh  # Linux

# This creates a self-contained package with:
# - Docker images
# - BGE embedding model
# - Python dependencies
# - Docker installer
```

See [README_OFFLINE.md](README_OFFLINE.md) for detailed instructions.

### Option 3: Development Mode

```bash
# Install Python dependencies
pip install -r requirements.txt

# Start databases (requires PostgreSQL, Neo4j, Redis)
docker compose up -d postgres neo4j redis

# Initialize database
python scripts/init_db.py

# Start backend
uvicorn src.api.app:app --host 0.0.0.0 --port 8889 --reload

# Start frontend (new terminal)
cd frontend-v2
npm install
npm run dev
```

## Project Structure

```
chip_fault_agent/
├── src/
│   ├── agents/              # Multi-Agent implementation
│   │   ├── agent1/         # Agent1 - Reasoning Core
│   │   ├── agent2/         # Agent2 - Expert Interaction
│   │   ├── workflow.py     # LangGraph orchestration
│   │   └── multi_turn_handler.py  # Multi-turn conversation
│   ├── mcp/                # MCP tools layer
│   │   └── tools/          # Tool implementations
│   ├── database/           # Database models & repositories
│   │   ├── models.py       # Core data models
│   │   ├── rbac_models.py  # RBAC permission models
│   │   └── migrations/     # Database migrations
│   ├── auth/               # Authentication & authorization
│   │   ├── service.py      # Auth service
│   │   ├── decorators.py   # Auth decorators
│   │   └── middleware.py   # Auth middleware
│   ├── api/                # FastAPI routes
│   │   ├── app.py          # Main application
│   │   ├── analyze_routes.py
│   │   ├── auth_routes.py
│   │   ├── admin_routes.py
│   │   ├── expert_routes.py
│   │   └── monitoring_routes.py
│   ├── embedding/          # BGE embedding manager
│   │   └── bge_manager.py  # Local BGE model wrapper
│   ├── monitoring/         # System monitoring
│   │   └── alerts.py       # Health check & alerting
│   └── config/             # Configuration management
├── frontend-v2/            # React + Vite frontend
│   ├── src/
│   │   ├── pages/
│   │   │   └── AnalyzePage.jsx
│   │   ├── components/
│   │   └── api.js
│   ├── Dockerfile.frontend
│   └── nginx.conf
├── docker-compose.yml      # Docker orchestration
├── Dockerfile.backend      # Backend container
├── Dockerfile.postgres     # PostgreSQL with pgvector
├── scripts/                # Utility scripts
│   ├── init_db.py
│   └── init_bge_model.py
├── sql/                    # Database initialization
└── docs/                   # Documentation
    └── BGE_EMBEDDING_GUIDE.md
```

## Configuration

Key environment variables (`.env.docker.template`):

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `ANTHROPIC_API_KEY` | Anthropic Claude API key | - | ✅ |
| `POSTGRES_HOST` | PostgreSQL host | postgres | - |
| `POSTGRES_DB` | Database name | chip_analysis | - |
| `NEO4J_URI` | Neo4j connection URI | bolt://neo4j:7687 | - |
| `REDIS_HOST` | Redis host | redis | - |
| `EMBEDDING_BACKEND` | Embedding backend | bge | - |
| `EMBEDDING_MODEL` | BGE model name | BAAI/bge-large-zh-v1.5 | - |
| `TRANSFORMERS_CACHE` | Model cache path | /app/models | - |
| `DEFAULT_CONFIDENCE_THRESHOLD` | Expert intervention threshold | 0.7 | - |

## API Documentation

### Authentication

| Endpoint | Method | Description |
|----------|--------|-------------|
| `POST /api/v1/auth/register` | Register | Create new user |
| `POST /api/v1/auth/login` | Login | Get access token |
| `POST /api/v1/auth/logout` | Logout | Invalidate session |
| `GET /api/v1/auth/me` | Get User | Current user info |

### Analysis

| Endpoint | Method | Description | Permission |
|----------|--------|-------------|------------|
| `POST /api/v1/analyze` | Submit | Analyze chip logs | `analysis:create` |
| `GET /api/v1/analysis/{id}` | Get Result | Fetch analysis result | `analysis:read` |
| `POST /api/v1/analyze/{id}/continue` | Continue | Multi-turn follow-up | `analysis:create` |
| `GET /api/v1/modules` | List | Supported modules | `analysis:read` |

### Expert Correction

| Endpoint | Method | Description | Permission |
|----------|--------|-------------|------------|
| `POST /api/v1/expert/corrections/{id}` | Submit | Submit expert correction | `expert_correction:create` |
| `POST /api/v1/expert/corrections/{id}/approve` | Approve | Approve correction (learns) | `expert_correction:approve` |
| `GET /api/v1/expert/knowledge/statistics` | Stats | Knowledge learning stats | `audit_log:read` |

### Monitoring

| Endpoint | Method | Description |
|----------|--------|-------------|
| `GET /api/v1/health` | Health | System health check |
| `GET /api/v1/monitoring/status` | Status | Service status |
| `GET /api/v1/monitoring/alerts` | Alerts | Active alerts |

## Supported Modules

| Module | Description | Subtypes |
|--------|-------------|----------|
| `cpu` | CPU Core | - |
| `l3_cache` | L3 Cache | - |
| `ha` | Coherence Agent | agent, snoop_filter, directory |
| `noc_router` | NoC Router | - |
| `ddr_controller` | DDR Controller | - |
| `hbm_controller` | HBM Controller | - |

## User Roles

| Role | Level | Description |
|------|-------|-------------|
| `super_admin` | 100 | Full system access |
| `admin` | 80 | User & role management |
| `expert` | 60 | Submit corrections & update knowledge |
| `analyst` | 40 | Submit analysis requests |
| `viewer` | 20 | Read-only access |

**Default Admin Account:**
- Username: `admin`
- Password: `admin123`

## Development

### Run Tests

```bash
# API tests
pytest tests/test_api.py

# Database tests
pytest tests/test_database.py

# Integration tests
pytest tests/test_integration.py
```

### Code Quality

```bash
# Format code
black src/ frontend-v2/src/

# Type checking
mypy src/

# Linting
flake8 src/
```

## Deployment

### Production Deployment

```bash
# Build production images
docker compose -f docker-compose.yml build

# Export for offline deployment
export-offline.bat

# On target machine
offline-import.bat
```

### Monitoring

```bash
# View logs
docker compose logs -f backend

# Check service health
curl http://localhost:8889/api/v1/health

# View metrics
docker compose ps
```

## Troubleshooting

### Common Issues

**1. BGE Model Loading Error**
```bash
# Download BGE model manually
python scripts/init_bge_model.py

# Or copy from cache
python copy-bge-model.py
```

**2. Database Connection Failed**
```bash
# Check PostgreSQL status
docker compose logs postgres

# Verify pgvector extension
docker exec -it chip-fault-postgres psql -U postgres -d chip_analysis
chip_analysis=# CREATE EXTENSION IF NOT EXISTS vector;
```

**3. High Memory Usage**
- BGE model requires ~4GB RAM
- Reduce `EMBEDDING_DEVICE` to CPU if GPU unavailable
- Increase Docker memory limit to 8GB+

## Documentation

- [System Architecture](SYSTEM_V2_TECHNICAL_SPEC.md) - Complete technical specification
- [Offline Deployment Guide](README_OFFLINE.md) - Air-gapped deployment
- [BGE Embedding Guide](docs/BGE_EMBEDDING_GUIDE.md) - Local embedding model
- [Docker Deployment](README_DOCKER_DEPLOY.md) - Container deployment
- [Troubleshooting](TROUBLESHOOTING_WINDOWS.md) - Common issues and solutions

## License

MIT License - see LICENSE file for details

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'feat: add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## Support

For issues and questions:
- GitHub Issues: https://github.com/xpengch/chip-fault-agent/issues
- Documentation: https://github.com/xpengch/chip-fault-agent/wiki

---

**Built with ❤️ for chip failure analysis**
