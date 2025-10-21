# Mock Data for Multi-Tenant Dashboards

This directory contains tenant-scoped test data for CLV and Risk Analysis dashboards.

## Data Structure

```
mock-data/
├── clv/
│   └── data.csv       # Customer Lifetime Value data (Acme only)
└── risk/
    └── data.csv       # Risk Analysis data (Acme + Beta)
```

## Tenant Distribution

### CLV Dashboard (customer-lifetime-value)
- **Acme Corporation** (8e1b3d5b-7c9a-4e2f-b1d3-a5c7e9f12345): 99 records
- **Beta Industries**: No access (demonstrates tenant isolation)

### Risk Dashboard (risk-analysis)
- **Acme Corporation** (8e1b3d5b-7c9a-4e2f-b1d3-a5c7e9f12345): ~60% of records
- **Beta Industries** (2450a2f8-3b7e-4eab-9b4a-1f73d9a0b1c4): ~40% of records

## Data Format

All CSV files include a `tenant_id` column for multi-tenant filtering.

### CLV Data Schema
Source: sample-plotly-repos/burn-performance-test-data/burn.csv
- Complex burn performance metrics with multiple dimensions
- 99 records total
- All records assigned to Acme tenant

### Risk Data Schema
Source: sample-plotly-repos/mixshift-test-data/mix.csv
- Transaction types, earn months, risk buckets
- 99 records total
- Split between Acme (60%) and Beta (40%)

## Data Augmentation

Data was augmented with tenant_id using `scripts/augment_data_with_tenants.py`:
- CLV: All records → Acme tenant_id
- Risk: 60/40 split → Acme/Beta tenant_ids

## Usage

Data is accessed via FastAPI Data API endpoint:
- GET /api/dashboards/{slug}/data
- Requires tenant-scoped JWT token
- Returns tenant-filtered records only
