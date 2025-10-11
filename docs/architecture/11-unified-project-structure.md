# 11. Unified Project Structure

```
kyros-saas-poc/
├── .github/                           # CI/CD workflows (future)
├── apps/                              # Application packages
│   ├── shell-ui/                      # Next.js Shell UI
│   ├── api/                           # FastAPI Monolith
│   ├── dash-app-clv/                  # Customer Lifetime Value Dashboard
│   └── dash-app-risk/                 # Risk Analysis Dashboard
├── packages/                          # Shared packages
│   └── shared-config/                 # ⭐ Shared JWT config (Python)
├── data/                              # Data and database files
│   ├── tenant_metadata.db             # SQLite database (generated)
│   └── mock-data/                     # Mock tenant data (CSV/Parquet)
├── database/                          # Database schemas and migrations
│   ├── schema.sql                     # SQLite schema with seed data
│   └── migrations/                    # Future PostgreSQL migrations
├── scripts/                           # Build/deploy/utility scripts
│   ├── seed-database.py               # Initialize database
│   ├── generate-mock-data.py          # Create CSV mock data
│   └── docker-entrypoint.sh           # Docker startup script
├── docs/                              # Documentation
│   ├── prd.md
│   ├── architecture.md                # This document
│   ├── brainstorming-session-results.md
│   └── existing-architecture-docs/    # Reference architecture
├── tests/                             # E2E tests (Playwright)
│   ├── e2e/
│   └── playwright.config.ts
├── .env.example                       # Environment template
├── docker-compose.yml                 # Orchestration
├── package.json                       # Root workspace config
├── README.md                          # Setup instructions
└── .gitignore
```

---
