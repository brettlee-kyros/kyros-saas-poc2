# Kyros SaaS PoC - Multi-Tenant Dashboard Platform

A proof-of-concept multi-tenant dashboard platform demonstrating JWT-based tenant isolation, token exchange flows, and embedded Plotly Dash applications within a Next.js Shell UI.

## Overview

This PoC validates the core architectural pattern for tenant-isolated dashboard embedding:

1. **User Authentication**: Mock authentication issues multi-tenant user access tokens
2. **Tenant Selection**: Shell UI allows users to select their active tenant
3. **Token Exchange**: Exchange user token for short-lived tenant-scoped tokens
4. **Dashboard Embedding**: Dash apps validate tenant tokens and serve filtered data
5. **Reverse Proxy**: Next.js API routes inject tenant tokens into Dash app requests

## Technology Stack

| Component | Technology | Version | Purpose |
|-----------|-----------|---------|---------|
| **Frontend** | Next.js | 14.2+ | Shell UI with App Router and SSR |
| **Frontend Language** | TypeScript | 5.3+ | Type-safe frontend development |
| **Styling** | Tailwind CSS | 3.4+ | Utility-first CSS framework |
| **Backend API** | FastAPI | 0.115+ | Python async API framework |
| **Backend Language** | Python | 3.11+ | API and dashboard applications |
| **Dashboard Framework** | Plotly Dash | 2.18+ | Interactive data visualization |
| **Database** | SQLite | 3.45+ | Tenant metadata (PostgreSQL-compatible schema) |
| **Authentication** | JWT (PyJWT) | 2.8+ | Token-based authentication |
| **Validation** | Pydantic | 2.5+ | Data validation and settings |
| **Orchestration** | Docker Compose | 2.29+ | Local multi-service deployment |
| **Linting (Python)** | Ruff | Latest | Fast Python linter and formatter |
| **Linting (TypeScript)** | ESLint | Latest | TypeScript/React linting |

## Project Structure

```
kyros-saas-poc/
├── apps/                              # Application packages
│   ├── shell-ui/                      # Next.js Shell UI (port 3000)
│   ├── api/                           # FastAPI Backend (port 8000)
│   ├── dash-app-clv/                  # Customer Lifetime Value Dashboard (port 8050)
│   └── dash-app-risk/                 # Risk Analysis Dashboard (port 8051)
├── packages/                          # Shared packages
│   └── shared-config/                 # Shared JWT configuration (Python)
├── data/                              # Data and database files
│   ├── tenant_metadata.db             # SQLite tenant metadata database
│   └── mock-data/                     # Mock tenant-scoped data (CSV/Parquet)
├── database/                          # Database schemas and migrations
│   ├── schema.sql                     # SQLite schema with seed data
│   └── migrations/                    # Future PostgreSQL migrations
├── scripts/                           # Build/deploy/utility scripts
│   ├── seed-database.py               # Initialize database with mock data
│   └── generate-mock-data.py          # Create mock tenant data files
├── tests/                             # End-to-end tests
│   ├── e2e/                           # Playwright E2E tests
│   └── playwright.config.ts           # Playwright configuration
├── docs/                              # Documentation
│   ├── prd/                           # Product requirements (epics/stories)
│   ├── architecture/                  # Architecture documentation
│   └── stories/                       # Development stories
├── .env.example                       # Environment variable template
├── docker-compose.yml                 # Docker Compose orchestration
├── package.json                       # Root npm workspace configuration
├── pyproject.toml                     # Python tooling configuration (Ruff)
└── README.md                          # This file
```

## Prerequisites

Before running the PoC, ensure you have the following installed:

- **Node.js**: 20+ (LTS) - [Download](https://nodejs.org/)
- **npm**: 10+ (included with Node.js)
- **Python**: 3.11+ - [Download](https://www.python.org/downloads/)
- **Docker**: 24+ (optional, for containerized deployment) - [Download](https://www.docker.com/)
- **Docker Compose**: 2.29+ (included with Docker Desktop)

### Verify Installation

```bash
node --version    # Should be v20.x.x or higher
npm --version     # Should be 10.x.x or higher
python --version  # Should be 3.11.x or higher
docker --version  # Should be 24.x.x or higher (if using Docker)
```

## Setup Instructions

### 1. Clone Repository

```bash
git clone <repository-url>
cd kyros-saas-poc
```

### 2. Install Node.js Dependencies

```bash
npm install
```

This installs all frontend dependencies for the Next.js Shell UI using npm workspaces.

### 3. Set Up Python Virtual Environment

It's recommended to use a virtual environment for Python dependencies:

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 4. Install Python Dependencies

Install dependencies for each Python application:

```bash
# Install shared config package (editable mode)
pip install -e packages/shared-config

# Install FastAPI dependencies
pip install -r apps/api/requirements.txt

# Install Dash app dependencies
pip install -r apps/dash-app-clv/requirements.txt
pip install -r apps/dash-app-risk/requirements.txt

# Install development tools
pip install pytest httpx ruff
```

### 5. Initialize Database

Create and seed the tenant metadata database:

```bash
python scripts/seed-database.py
```

Verify database creation:

```bash
python scripts/validate-database.py
```

### 6. Configure Environment Variables

Copy the example environment file:

```bash
cp .env.example .env.local
```

Edit `.env.local` with your configuration (defaults should work for local development).

## Development Commands

### Start All Services (Development Mode)

```bash
npm run dev
```

This starts all development servers concurrently (once implemented in Story 1.6+).

### Build All Applications

```bash
npm run build
```

### Run Linting

**TypeScript/React:**
```bash
npm run lint
```

**Python:**
```bash
npm run lint:python
# Or directly: ruff check apps/ packages/
```

### Run Tests

**Unit Tests:**
```bash
npm run test
```

**Python Tests:**
```bash
pytest apps/api/tests/ -v
pytest packages/shared-config/tests/ -v
```

**E2E Tests:**
```bash
npx playwright test
```

## Docker Compose Quick Start

The easiest way to run the entire PoC is using Docker Compose:

```bash
# Build and start all services
docker-compose up --build

# Run in background
docker-compose up --build -d

# View logs
docker-compose logs -f

# Stop all services
docker-compose down
```

### Service Ports

Once running, access the services at:

- **Shell UI**: http://localhost:3000
- **FastAPI API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs (Swagger UI)
- **CLV Dashboard**: http://localhost:8050
- **Risk Dashboard**: http://localhost:8051

## Documentation

- **Product Requirements**: [docs/prd/](docs/prd/)
- **Architecture**: [docs/architecture/](docs/architecture/)
- **Development Stories**: [docs/stories/](docs/stories/)
- **Epic 1 (Foundation)**: [docs/prd/epic-1-foundation-shared-configuration.md](docs/prd/epic-1-foundation-shared-configuration.md)

## Development Workflow

### Story-Based Development

Development follows an epic-based story workflow:

1. **Epic 0**: Prerequisites & validation (completed)
2. **Epic 1**: Foundation & shared configuration (current)
3. **Epic 2**: Authentication & token exchange
4. **Epic 3**: Tenant metadata & data access
5. **Epic 4**: Dashboard embedding & integration
6. **Epic 5**: End-to-end testing & polish

Each story has detailed tasks in `docs/stories/`.

### Testing Strategy

- **Unit Tests**: Component and API endpoint tests
- **Integration Tests**: Database and service interaction tests
- **E2E Tests**: Full user flows with Playwright

## Mock Users and Tenants

The seeded database includes mock data for testing:

### Mock Tenants

| Tenant Name | Slug | Dashboards |
|------------|------|-----------|
| Acme Corporation | `acme-corp` | CLV, Risk Analysis |
| Beta Industries | `beta-ind` | Risk Analysis |

### Mock Users

| Email | Password | Tenant Access | Role |
|-------|----------|--------------|------|
| `analyst@acme.com` | `demo123` | Acme only | Viewer |
| `admin@acme.com` | `demo123` | Acme, Beta | Admin |
| `viewer@beta.com` | `demo123` | Beta only | Viewer |

## Troubleshooting

### Port Already in Use

If you see "port already in use" errors:

```bash
# Check what's using the port
lsof -i :3000  # or :8000, :8050, :8051

# Kill the process or change ports in docker-compose.yml
```

### Database Not Found

If the API can't connect to the database:

```bash
# Re-run the seed script
python scripts/seed-database.py

# Verify database exists
ls -la data/tenant_metadata.db
```

### Python Module Not Found

If you see "module not found" errors:

```bash
# Ensure virtual environment is activated
source venv/bin/activate

# Reinstall shared-config in editable mode
pip install -e packages/shared-config
```

### Docker Build Failures

If Docker builds fail:

```bash
# Clean Docker cache and rebuild
docker-compose down -v
docker system prune -a
docker-compose up --build
```

## License

UNLICENSED - Internal PoC Only

## Contact

For questions or issues, please refer to the project documentation in `docs/`.
