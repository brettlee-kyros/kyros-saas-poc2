# 12. Development Workflow

## 12.1 Prerequisites

```bash
# Required software
node --version    # v20+ required
npm --version     # v10+ required
python --version  # 3.11+ required
docker --version  # 24+ required
docker-compose --version  # 2.29+ required
```

## 12.2 Initial Setup

```bash
# Clone repository
git clone <repo-url> kyros-saas-poc
cd kyros-saas-poc

# Install shared config package (make it available to Python apps)
cd packages/shared-config
pip install -e .
cd ../..

# Install dependencies
npm install                    # Installs shell-ui dependencies
cd apps/api && pip install -r requirements.txt && cd ../..
cd apps/dash-app-clv && pip install -r requirements.txt && cd ../..
cd apps/dash-app-risk && pip install -r requirements.txt && cd ../..

# Initialize database
python scripts/seed-database.py

# Generate mock data (if not committed to repo)
python scripts/generate-mock-data.py

# Copy environment template
cp .env.example .env
# Edit .env with appropriate values
```

## 12.3 Development Commands

```bash
# Start all services (Docker Compose)
docker-compose up --build

# Run tests
npm run test                    # Frontend unit tests (Vitest)
cd apps/api && pytest          # Backend unit tests
npm run test:e2e               # E2E tests (Playwright)

# Reset database to clean state
python scripts/seed-database.py
```

---
