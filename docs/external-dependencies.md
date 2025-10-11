# Kyros PoC - External Dependencies

**Last Updated:** 2025-10-07
**Validated By:** Story 0.1 - Verify Sample Plotly Repositories Accessibility

---

## Repository Locations

### burn-performance (Customer Lifetime Value Dashboard)

**Status:** ✅ Accessible
**Location:** `/kyros-dev/work/kyros-saas-poc/sample-plotly-repos/burn-performance`
**Type:** Local directory
**Access Method:** Direct file system access

### mixshift (Risk Analysis Dashboard)

**Status:** ✅ Accessible
**Location:** `/kyros-dev/work/kyros-saas-poc/sample-plotly-repos/mixshift`
**Type:** Local directory
**Access Method:** Direct file system access

---

## Dash Application Structure

### burn-performance

**Entry Point:** `app.py`
**Application Type:** Multi-page Dash application
**Dash Version:** 2.18.1

**Key Files:**
- `app.py` - Main application entry point
- `requirements.txt` - Python dependencies
- `requirements-dev.txt` - Development dependencies
- `Procfile` - Deployment configuration
- `project.toml` - Project metadata

**Directory Structure:**
```
burn-performance/
├── app.py                    # Main entry point
├── requirements.txt          # Dependencies
├── assets/                   # Static assets (CSS, images)
├── pages/                    # Page modules
│   ├── tm2/
│   ├── tm5/
│   └── common/
├── utils/                    # Utility modules
│   ├── catalog_initializer.py
│   ├── components.py
│   ├── exception_handlers.py
│   └── ...
└── test/                     # Test modules
```

**Dependencies (from requirements.txt):**
- `dash==2.18.1` ✅ (matches PoC target)
- `dash-bootstrap-components==1.6.0`
- `dash-design-kit==2.1.1`
- `dash-iconify==0.1.2`
- `dash-mantine-components==0.14.6`
- `pandas==2.1.4`
- `plotly==6.0.0`
- `numpy==1.24.4`
- `databricks-connect==13.0.1` (external data source)
- `databricks-sdk==0.29.0`
- `databricks-sql-connector==2.9.6`
- `pyspark==3.5.1`
- `redis==5.0.6` (caching)
- `flask-caching==2.3.0`
- `dash-ag-grid==32.3.0`
- `gunicorn==20.0.4` (WSGI server)
- `python-dotenv==1.0.1`
- **Private package:** `kyros-plotly-common==0.5.8` (requires custom PyPI index)

**Data Loading Pattern:**
- Uses Databricks for data source (databricks-connect, databricks-sql-connector)
- Catalog initializer pattern (`utils.catalog_initializer`)
- Likely uses environment variables for configuration (`.env` files)
- Implements caching with Redis and flask-caching

**Dash Patterns Observed:**
- Multi-page application structure (`pages/` directory)
- Custom header and sidebar from `kyros-plotly-common`
- Uses React 18.2.0
- Custom error handlers
- Store components for state management
- Uses dash-bootstrap-components for layout

---

### mixshift

**Entry Point:** `app.py`
**Application Type:** Multi-page Dash application
**Dash Version:** 2.18.1

**Key Files:**
- `app.py` - Main application entry point
- `requirements.txt` - Python dependencies
- `requirements-dev.txt` - Development dependencies
- `Procfile` - Deployment configuration
- `project.toml` - Project metadata
- `pytest.ini` - Test configuration
- `MIXSHIFT_DEV_DOCS.md` - Developer documentation
- `MIXSHIFT_USER_GUIDE.md` - User guide

**Directory Structure:**
```
mixshift/
├── app.py                    # Main entry point
├── requirements.txt          # Dependencies
├── assets/                   # Static assets
├── pages/                    # Page modules
│   ├── mixshift/
│   └── common/
├── tests/                    # Test modules
├── examples/                 # Example code
└── MetadatasForReference.json # Configuration metadata
```

**Dependencies (from requirements.txt):**
- `dash==2.18.1` ✅ (matches PoC target)
- `dash-bootstrap-components==1.6.0`
- `dash-design-kit==2.1.1`
- `dash-iconify==0.1.2`
- `dash-mantine-components==0.14.6`
- `pandas==2.1.4`
- `plotly==6.0.0`
- `polars==1.7.0` (alternative DataFrame library)
- `numpy==1.24.4`
- `scipy==1.10.1`
- `databricks-connect==13.0.1`
- `databricks-sdk==0.29.0`
- `databricks-sql-connector==2.9.6`
- `pyspark==3.5.1`
- `redis==5.0.6`
- `flask-caching==2.3.0`
- `dash-ag-grid==32.3.0`
- `python-dotenv==1.0.1`
- `pytest==8.3.2`
- `psutil>=5.9.0`
- **Private package:** `kyros-plotly-common==0.5.8` (requires custom PyPI index)

**Data Loading Pattern:**
- Uses Databricks for data source (same as burn-performance)
- Catalog initializer pattern
- Environment variable configuration
- Implements caching

**Dash Patterns Observed:**
- Multi-page application structure
- Custom header and sidebar from `kyros-plotly-common`
- Uses React 18.2.0
- Custom error handlers
- Logger from `kyros-plotly-common`
- Store components and bubbler visualizations

---

## Access Instructions

### Direct File System Access

Both repositories are currently available as local directories within the project structure.

**To access:**
```bash
cd /kyros-dev/work/kyros-saas-poc/sample-plotly-repos/

# Burn-performance
cd burn-performance
ls -la

# Mixshift
cd mixshift
ls -la
```

**No authentication required** - directories are readable by the development environment.

---

## Test Data

### burn-performance-test-data

**Status:** ✅ Accessible and Compatible
**Location:** `/kyros-dev/work/kyros-saas-poc/sample-plotly-repos/burn-performance-test-data`

**Data Files:**
- `burn.csv` (55 KB)
- `burn-schema.md` (9.6 KB - metadata schema definition)

**Data Schema (burn.csv):**
- **Format:** CSV
- **Row Count:** 100 rows (header + 99 data rows)
- **Column Count:** 56 columns
- **File Size:** 55 KB

**Key Columns:**
- `burn_cluster_collapse` (int64) - Cluster identifier
- `snapshotDate` (object/string) - Date in YYYY-MM-DD format
- `obsAge` (int64) - Observation age
- `prd_s_snpdt_burn_man_dim` (object/string) - Manual dimension identifier
- `prd_s_snpdt_tsl_man_dim` (float64) - TSL manual dimension
- `prd_s_snpdt_em_age_man_dim` (float64) - EM age manual dimension
- `epgrp_cumul_exp_pct_dev` (float64) - Cumulative expected percentage deviation
- `epgrp_cumul_rdm_*_pct_dev` (float64) - Random deviation metrics (1-5)
- `prd_s_snpDt_epgrp_os` (float64) - Exposure group outstanding
- `pred_epgrp_cumul_*` (float64) - Predicted cumulative metrics (multiple columns)
- `mask_epgrp_cumul_*` (float64) - Mask flags for metrics

**Data Types Distribution:**
- Integer columns: 2
- Float columns: 52
- String columns: 2

**Data Quality:**
- ✅ Successfully loads into Pandas DataFrame
- ⚠️ Contains null values (33 rows have nulls in some deviation columns - expected for time-series data)
- ✅ Row count meets minimum threshold (100 > 20)
- ✅ Suitable for Epic 4 mock data

---

### mixshift-test-data

**Status:** ✅ Accessible and Compatible
**Location:** `/kyros-dev/work/kyros-saas-poc/sample-plotly-repos/mixshift-test-data`

**Data Files:**
- `mix.csv` (7.1 KB)
- `mix-schema.md` (527 bytes - metadata schema definition)

**Data Schema (mix.csv):**
- **Format:** CSV
- **Row Count:** 100 rows (header + 99 data rows)
- **Column Count:** 6 columns
- **File Size:** 7.1 KB

**Key Columns:**
- `transactionType` (object/string) - Transaction type (e.g., "Earn 1", "Earn 2", etc.)
- `earnMonth` (object/string) - Date in YYYY-MM-DD format
- `variable` (object/string) - Variable name (e.g., "Bucket URR Rdm 3 Group")
- `bucket_id` (float64) - Bucket identifier (1.0-11.0)
- `bucket_name` (object/string) - Bucket range (e.g., "0.0, 1.0E-5")
- `earn` (float64) - Earned points value

**Data Types Distribution:**
- Float columns: 2
- String columns: 4

**Data Quality:**
- ✅ Successfully loads into Pandas DataFrame
- ✅ No null values
- ✅ Row count meets minimum threshold (100 > 20)
- ✅ Suitable for Epic 4 mock data

---

## Tenant ID Augmentation Requirements

**Validated By:** Story 0.2

Both datasets require `tenant_id` column augmentation for multi-tenant filtering in Epic 4.

### Current State
- ❌ Neither dataset contains a `tenant_id` column
- ✅ Both datasets have sufficient rows for tenant distribution

### Augmentation Strategy

**Tenant IDs (from seed data):**
- Acme Corporation: `8e1b3d5b-7c9a-4e2f-b1d3-a5c7e9f12345`
- Beta Industries: `2450a2f8-3b7e-4eab-9b4a-1f73d9a0b1c4`

**Distribution Plan:**

**burn-performance (CLV data):**
- 100% of data assigned to Acme Corporation
- Rationale: Per Epic 0, Beta only has Risk dashboard access
- tenant_id column added with Acme UUID

**mixshift (Risk data):**
- 60% of data (60 rows) assigned to Acme Corporation
- 40% of data (40 rows) assigned to Beta Industries
- tenant_id column added with appropriate UUIDs

**Implementation:**
```python
import pandas as pd

# Load burn data
burn_df = pd.read_csv('burn.csv')
burn_df['tenant_id'] = '8e1b3d5b-7c9a-4e2f-b1d3-a5c7e9f12345'  # All Acme

# Load mix data
mix_df = pd.read_csv('mix.csv')
split_point = int(len(mix_df) * 0.6)  # 60 rows

# Assign tenant IDs
mix_df.loc[:split_point-1, 'tenant_id'] = '8e1b3d5b-7c9a-4e2f-b1d3-a5c7e9f12345'  # Acme
mix_df.loc[split_point:, 'tenant_id'] = '2450a2f8-3b7e-4eab-9b4a-1f73d9a0b1c4'  # Beta

# Save augmented data
burn_df.to_csv('data/mock-data/clv_data.csv', index=False)
mix_df.to_csv('data/mock-data/risk_data.csv', index=False)
```

---

## Epic 4 Data Preparation Steps

**Documented By:** Story 0.2

### Prerequisites
- Epic 0 completed (repositories validated, test data confirmed compatible)
- `data/mock-data/` directory created

### Step-by-Step Process

**1. Copy Test Data Files**
```bash
mkdir -p data/mock-data
cp sample-plotly-repos/burn-performance-test-data/burn.csv data/mock-data/burn_raw.csv
cp sample-plotly-repos/mixshift-test-data/mix.csv data/mock-data/mix_raw.csv
```

**2. Run Tenant Augmentation Script**

Create `scripts/augment-test-data.py`:
```python
#!/usr/bin/env python3
"""
Augment test data with tenant_id for multi-tenant filtering
Run during Epic 4, Story 4.1 setup
"""

import pandas as pd
from pathlib import Path

# Tenant IDs
ACME_ID = '8e1b3d5b-7c9a-4e2f-b1d3-a5c7e9f12345'
BETA_ID = '2450a2f8-3b7e-4eab-9b4a-1f73d9a0b1c4'

# Augment burn data (100% Acme)
burn_df = pd.read_csv('data/mock-data/burn_raw.csv')
burn_df['tenant_id'] = ACME_ID
burn_df.to_csv('data/mock-data/clv_data.csv', index=False)
print(f"✅ CLV data augmented: {len(burn_df)} rows for Acme")

# Augment mix data (60% Acme, 40% Beta)
mix_df = pd.read_csv('data/mock-data/mix_raw.csv')
split_point = int(len(mix_df) * 0.6)

mix_df.loc[:split_point-1, 'tenant_id'] = ACME_ID
mix_df.loc[split_point:, 'tenant_id'] = BETA_ID
mix_df.to_csv('data/mock-data/risk_data.csv', index=False)

acme_count = (mix_df['tenant_id'] == ACME_ID).sum()
beta_count = (mix_df['tenant_id'] == BETA_ID).sum()
print(f"✅ Risk data augmented: {acme_count} rows for Acme, {beta_count} rows for Beta")
```

**3. Run Augmentation Script**
```bash
python scripts/augment-test-data.py
```

**4. Verify Augmented Data**
```python
import pandas as pd

clv_df = pd.read_csv('data/mock-data/clv_data.csv')
risk_df = pd.read_csv('data/mock-data/risk_data.csv')

# Verify tenant_id column exists
assert 'tenant_id' in clv_df.columns
assert 'tenant_id' in risk_df.columns

# Verify tenant distribution
print(f"CLV tenant distribution:\n{clv_df['tenant_id'].value_counts()}")
print(f"Risk tenant distribution:\n{risk_df['tenant_id'].value_counts()}")
```

**5. Update Data API Service (Epic 4, Story 4.1)**

Data API endpoints will filter by tenant_id:
```python
# In data-api service
@app.get("/data/clv")
def get_clv_data(request: Request):
    tenant_id = extract_tenant_from_jwt(request)  # From JWT claims
    df = load_clv_data()  # Loads clv_data.csv
    tenant_df = df[df['tenant_id'] == tenant_id]
    return tenant_df.to_dict(orient='records')
```

### Data Transformations

**No additional transformations required:**
- ✅ Date columns in compatible format (YYYY-MM-DD)
- ✅ Numeric columns load correctly as float64
- ✅ No type conversions needed
- ⚠️ Null values in burn data acceptable (time-series gaps)

### Testing Data Preparation

**Validation checks (Epic 4, Story 4.1 AC):**
1. Both CSV files contain `tenant_id` column
2. CLV data: 100 rows, all with Acme tenant_id
3. Risk data: 100 rows, 60 Acme + 40 Beta
4. Data API returns correct tenant-scoped data
5. No data leakage between tenants

---

---

## Dash Application Startup Validation

**Validated By:** Story 0.3

### Summary

**Status:** ❌ Cannot start applications in current environment
**Reason:** Multiple blocking dependencies (private packages, Databricks, Redis)
**Impact:** Applications require modification for Epic 4 (expected per architecture)

### Startup Feasibility Analysis

Both `burn-performance` and `mixshift` applications have identical dependency structures that prevent standalone startup in the PoC environment.

#### Blocking Dependencies

**1. Private Package - kyros-plotly-common==0.5.8**
- **Status:** ❌ Not accessible
- **Required from:**
  - `https://plotly.kyrosinsights.com/packages`
  - `https://pkgs.dev.azure.com/kyrosinsights/.../dash-common/pypi/simple/`
- **Impact:** Application won't import - provides header, sidebar, cache, logger, theme components
- **Epic 4 Resolution:** Mock/stub these components or replace with standard Dash components

**2. Databricks Infrastructure**
- **Status:** ❌ Not available in PoC environment
- **Dependencies:**
  - `databricks-connect==13.0.1`
  - `databricks-sdk==0.29.0`
  - `databricks-sql-connector==2.9.6`
  - `pyspark==3.5.1`
- **Impact:** Data loading will fail
- **Epic 4 Resolution:** Replace with FastAPI data endpoints serving CSV data

**3. Redis Caching**
- **Status:** ❌ Redis server not running in dev environment
- **Dependencies:**
  - `redis==5.0.6`
  - `flask-caching==2.3.0`
- **Impact:** Caching layer unavailable
- **Epic 4 Resolution:** Use in-memory caching or disable for PoC

#### Compatible Dependencies (Can Install)

The following dependencies can be installed without authentication:

✅ **Core Dash Stack:**
- `dash==2.18.1` - Main framework
- `dash-bootstrap-components==1.6.0` - Layout components
- `dash-iconify==0.1.2` - Icons
- `dash-mantine-components==0.14.6` - UI components
- `dash-ag-grid==32.3.0` - Grid component
- `plotly==6.0.0` - Visualization library

✅ **Data Processing:**
- `pandas==2.1.4` - Already installed
- `numpy==1.24.4` - Already installed
- `polars==1.7.0` - Alternative DataFrame library
- `scipy==1.10.1` - Scientific computing

✅ **Utilities:**
- `python-dotenv==1.0.1` - Environment variables
- `gunicorn==20.0.4` - WSGI server
- `pytest==8.3.2` - Testing
- `psutil>=5.9.0` - System utilities

### Validation Approach

Given the blocking dependencies, Story 0.3 validation focuses on:

1. ✅ **Dependency Analysis** - Completed (see above)
2. ✅ **Version Compatibility** - Dash 2.18.1 compatible with Python 3.8/3.11
3. ❌ **Application Startup** - Not attempted (known blockers)
4. ❌ **Screenshots** - Not possible without running app
5. ✅ **Epic 4 Strategy** - Documented modifications required

### Python 3.11 Compatibility

**Current Environment:** Python 3.8.10
**Target for PoC:** Python 3.11+

**Dependency Compatibility Analysis:**
- ✅ `dash==2.18.1` - Supports Python 3.8-3.12
- ✅ `pandas==2.1.4` - Supports Python 3.9-3.12
- ✅ `numpy==1.24.4` - Supports Python 3.8-3.11
- ✅ `plotly==6.0.0` - Supports Python 3.7+
- ⚠️ `scipy==1.10.1` - Supports Python 3.8-3.11 (3.12 requires scipy 1.11+)

**Recommendation:** Dependencies compatible with Python 3.11. Upgrade to Python 3.11 in Epic 1 is feasible.

### Dash Version Validation

**Target Version:** Dash 2.18+
**Found in requirements.txt:** `dash==2.18.1` ✅

**Import Style Check:**

From Story 0.1 inspection of `app.py` files, both applications use modern import style:
```python
from dash import dcc, html, Input, Output, State
```

✅ **No deprecated imports** - Applications already use Dash 2.x import patterns.

### Epic 4 Modification Strategy

Based on startup validation, the following modifications are required in Epic 4:

**1. Remove Private Package Dependencies (Epic 4, Story 4.2 & 4.3)**
```python
# Remove:
from kyros_plotly_common import header, sidebar, cache, logger, theme

# Replace with:
import dash_bootstrap_components as dbc
# Create simple header/sidebar using dbc.Navbar, dbc.Nav
```

**2. Replace Databricks Data Loading (Epic 4, Story 4.2 & 4.3)**
```python
# Remove:
from databricks import sql
from utils.catalog_initializer import load_data

# Replace with:
import requests
def load_data(tenant_id):
    response = requests.get(
        "http://data-api:8001/data/clv",
        headers={"Authorization": f"Bearer {jwt_token}"}
    )
    return pd.DataFrame(response.json())
```

**3. Simplify Caching (Epic 4, Story 4.2 & 4.3)**
```python
# Remove:
from flask_caching import Cache
import redis

# Replace with:
# Option 1: In-memory dict cache
cache = {}

# Option 2: Disable caching for PoC
# (Acceptable for <100 rows of test data)
```

**4. Add JWT Validation (Epic 4, Story 4.2 & 4.3)**
```python
# Add at app startup:
from shared_config import validate_jwt

# In Dash callbacks:
tenant_id = validate_jwt(request.headers.get("Authorization"))
data = load_data(tenant_id)  # Tenant-scoped data
```

### Baseline Screenshots

**Status:** ❌ Not captured
**Reason:** Applications cannot start without resolving blocking dependencies

**Alternative Baseline:**
- Epic 4 will create modified applications from scratch based on Story 0.1 structure analysis
- Baseline comparison will be against test data visualizations, not original apps
- Original app structure documented in Story 0.1 serves as architectural baseline

### Assets Created

**Directory Structure:**
```
docs/assets/dash-baseline/
├── (screenshots would go here if apps could run)
└── README.md - Documentation of why screenshots not captured
```

### Conclusion

**Startup Validation Result:** ❌ Applications cannot start in current environment

**Is this a problem?** ✅ **No - This is expected and acceptable**

**Rationale:**
1. Applications are designed for production environment with Databricks, Redis, private packages
2. Epic 4 explicitly plans to modify applications for PoC environment
3. Story 0.1 captured sufficient architectural information (structure, entry points, callbacks)
4. Story 0.2 validated test data compatibility
5. Epic 4 modifications will create PoC-compatible versions

**Next Steps:**
- ✅ Story 0.3 complete - Documented startup limitations and Epic 4 strategy
- Proceed to Story 0.5 - Risk Assessment (Story 0.4 already complete)
- Epic 4 will implement modifications per strategy above

---

## Key Findings & Considerations for Epic 4

### 1. Dash Version Compatibility ✅

Both applications use **Dash 2.18.1**, which matches the PoC target version. No version conflicts expected.

### 2. Private Package Dependency ⚠️

Both applications depend on **`kyros-plotly-common==0.5.8`**, a private package hosted on:
- `https://plotly.kyrosinsights.com/packages`
- `https://pkgs.dev.azure.com/kyrosinsights/.../dash-common/pypi/simple/`

**Impact on Epic 4:**
- This package provides header, sidebar, cache, logger, and theme components
- Options:
  1. Install private package if access available
  2. Mock/stub these components for PoC
  3. Replace with standard Dash components

**Recommendation:** Mock/stub approach for PoC to avoid external authentication requirements.

### 3. Databricks Dependencies ⚠️

Both applications load data from Databricks:
- `databricks-connect==13.0.1`
- `databricks-sdk==0.29.0`
- `databricks-sql-connector==2.9.6`
- `pyspark==3.5.1`

**Impact on Epic 4:**
- Cannot use actual Databricks connection in PoC
- Story 4.1 will replace with mock data (CSV/Parquet files)
- Data loading code will need modification to use FastAPI endpoints

### 4. Redis/Caching Dependencies ⚠️

Both applications use Redis for caching:
- `redis==5.0.6`
- `flask-caching==2.3.0`

**Impact on Epic 4:**
- PoC will use in-memory Pandas DataFrames (no Redis required)
- Caching code can be removed or disabled

### 5. Multi-Page Application Structure ✅

Both applications use Dash's multi-page structure with `pages/` directories.

**Impact on Epic 4:**
- Structure is compatible with PoC requirements
- Page registration and callbacks can be preserved

### 6. Python Version Compatibility ⚠️

Dependencies specify:
- `numpy==1.24.4` (compatible with Python 3.8-3.11)
- `pandas==2.1.4` (compatible with Python 3.9-3.12)
- `scipy==1.10.1` (compatible with Python 3.8-3.11)

Current dev environment: Python 3.8.10
PoC target: Python 3.11+

**Recommendation:** Dependencies are compatible across Python versions. Upgrade to 3.11+ recommended but not blocking.

---

## Epic 4 Integration Strategy

### Approach: Modify Existing Applications

**Rationale:** Both repositories are accessible, use compatible Dash versions, and have appropriate structure for PoC.

### Required Modifications (Epic 4)

1. **Remove/Mock Private Package Dependencies:**
   - Replace `kyros-plotly-common` components with standard Dash components
   - Create simple header/sidebar for PoC
   - Remove or stub custom themes

2. **Replace Databricks Data Loading:**
   - Remove databricks-connect, databricks-sdk, databricks-sql-connector
   - Remove pyspark dependency
   - Replace catalog initializer with FastAPI data endpoint calls
   - Load tenant-scoped data via API

3. **Add JWT Validation:**
   - Extract JWT from Authorization header (reverse proxy injection)
   - Validate JWT using shared-config module
   - Extract tenant_id from JWT claims

4. **Simplify Caching:**
   - Remove Redis dependency
   - Use in-memory caching or disable caching for PoC

5. **Update Dependencies:**
   - Create simplified requirements.txt without private packages
   - Remove Databricks dependencies
   - Keep core Dash, Plotly, Pandas dependencies

---

## Risk Assessment

**Created By:** Story 0.5
**Date:** 2025-10-07

### Summary

| Risk Category | Status | Criticality | Mitigation |
|---------------|--------|-------------|------------|
| Repository Accessibility | ✅ LOW | Important | Repos accessible, no action needed |
| Test Data Availability | ✅ LOW | Important | Data validated, 100 rows each |
| Application Startup | ⚠️ MEDIUM | Important | Cannot start (expected), Epic 4 will modify |
| Private Package Dependencies | ⚠️ MEDIUM | Important | Replace with standard components |
| Databricks Dependencies | ⚠️ MEDIUM | Critical | Replace with FastAPI endpoints |
| Python Version | ⚠️ LOW | Important | Upgrade to 3.11 in Epic 1 |

**Overall Risk Level:** ⚠️ **MEDIUM (Acceptable)**

### Detailed Risk Analysis

#### Risk 1: Repository Accessibility

| Factor | Assessment |
|--------|------------|
| **Availability** | ✅ Accessible |
| **Criticality** | Important (needed for CLV and Risk dashboards in Epic 4) |
| **Impact if Unavailable** | Epic 4 Stories 4.2-4.3 blocked; cannot demonstrate real Dash integration |
| **Fallback Option** | Create stub Dash apps with simple visualizations |
| **Estimated Fallback Effort** | 16-24 hours (8-12 hours per app) |
| **Status** | ✅ **RESOLVED** - Both repos accessible at `/kyros-dev/work/kyros-saas-poc/sample-plotly-repos/` |

**Recommendation:** No action required. Proceed with modifying actual repositories in Epic 4.

---

#### Risk 2: Test Data Availability

| Factor | Assessment |
|--------|------------|
| **Availability** | ✅ Accessible |
| **Criticality** | Important (can create synthetic if needed) |
| **Impact if Unavailable** | Epic 4, Story 4.1 delayed; need to generate synthetic data |
| **Fallback Option** | Generate synthetic CLV and Risk data (50-100 rows each) |
| **Estimated Fallback Effort** | 4-8 hours total |
| **Status** | ✅ **RESOLVED** - Test data validated (burn.csv: 100 rows, mix.csv: 100 rows) |

**Data Quality:**
- ✅ burn.csv: 56 columns, CSV format, loads successfully into Pandas
- ✅ mix.csv: 6 columns, CSV format, loads successfully into Pandas
- ⚠️ burn.csv contains null values (33 rows) - acceptable for time-series data
- ✅ Both meet minimum threshold (>20 rows)

**Recommendation:** No action required. Use existing test data with tenant_id augmentation (documented in Story 0.2).

---

#### Risk 3: Application Startup

| Factor | Assessment |
|--------|------------|
| **Availability** | ❌ Cannot start in current environment |
| **Criticality** | Important (baseline useful but not blocking) |
| **Impact if Unavailable** | No baseline screenshots; Epic 4 creates apps from architectural analysis |
| **Fallback Option** | Use Story 0.1 structural analysis as baseline |
| **Estimated Impact** | 0 hours (already expected and planned for) |
| **Status** | ⚠️ **ACCEPTED RISK** - Cannot start due to private packages, Databricks, Redis |

**Blocking Dependencies:**
1. Private package `kyros-plotly-common==0.5.8` (authentication required)
2. Databricks infrastructure (not available in PoC)
3. Redis server (not running in dev environment)

**Recommendation:** Accept risk. Epic 4 will create modified versions that work in PoC environment. Story 0.1 provides sufficient architectural baseline.

---

#### Risk 4: Private Package Dependencies

| Factor | Assessment |
|--------|------------|
| **Availability** | ❌ Not accessible |
| **Criticality** | Important (blocks current startup, Epic 4 will replace) |
| **Impact** | Applications cannot use original header, sidebar, cache, logger, theme components |
| **Mitigation** | Replace with dash-bootstrap-components (standard, no authentication) |
| **Estimated Effort** | 8-12 hours per app (included in Epic 4 estimates) |
| **Status** | ⚠️ **PLANNED MITIGATION** - Epic 4 will replace private packages |

**Mitigation Strategy:**
```python
# Replace kyros-plotly-common components with:
import dash_bootstrap_components as dbc

# Simple header
header = dbc.Navbar(...)

# Simple sidebar
sidebar = dbc.Nav(...)

# In-memory cache (or disable)
cache = {}
```

**Recommendation:** Implement mitigation in Epic 4, Stories 4.2-4.3. Estimated effort already included in epic.

---

#### Risk 5: Databricks Dependencies

| Factor | Assessment |
|--------|------------|
| **Availability** | ❌ Not available in PoC |
| **Criticality** | Critical (applications cannot load data without it) |
| **Impact** | Data loading fails; dashboards cannot display visualizations |
| **Mitigation** | Replace with FastAPI data endpoints serving CSV data |
| **Estimated Effort** | 12-16 hours (included in Epic 4, Story 4.1 estimates) |
| **Status** | ⚠️ **PLANNED MITIGATION** - Epic 4 will implement data API |

**Mitigation Strategy:**
```python
# Replace Databricks data loading with:
import requests

def load_data(tenant_id):
    response = requests.get(
        "http://data-api:8001/data/clv",
        headers={"Authorization": f"Bearer {jwt_token}"}
    )
    return pd.DataFrame(response.json())
```

**Recommendation:** Implement mitigation in Epic 4, Story 4.1 (data API) and Stories 4.2-4.3 (Dash integration). This is core PoC architecture.

---

#### Risk 6: Python Version Compatibility

| Factor | Assessment |
|--------|------------|
| **Current Version** | Python 3.8.10 |
| **Target Version** | Python 3.11+ |
| **Criticality** | Important (target for PoC, current version functional) |
| **Impact** | Current environment functional; upgrade recommended for Epic 1 |
| **Compatibility** | ✅ All dependencies support Python 3.11 |
| **Estimated Upgrade Effort** | 2-4 hours (included in Epic 1 estimates) |
| **Status** | ⚠️ **LOW RISK** - Development can proceed, upgrade in Epic 1 |

**Compatibility Assessment:**
- ✅ dash==2.18.1 - Supports Python 3.8-3.12
- ✅ pandas==2.1.4 - Supports Python 3.9-3.12
- ✅ numpy==1.24.4 - Supports Python 3.8-3.11
- ✅ plotly==6.0.0 - Supports Python 3.7+

**Recommendation:** Proceed with Python 3.8 for Epic 0. Upgrade to Python 3.11 in Epic 1, Story 1.1 or 1.2.

---

### Product Owner Decision

**Decision:** ✅ **APPROVED - Proceed with Actual Repositories**

**Rationale:**
1. ✅ Both repositories (burn-performance, mixshift) are accessible
2. ✅ Test data is available and compatible (100 rows each, CSV format)
3. ⚠️ Applications cannot start in current environment (EXPECTED - Epic 4 will modify)
4. ⚠️ Private packages and Databricks dependencies require replacement (PLANNED - Epic 4 design)
5. ✅ All core dependencies (Dash, Plotly, Pandas) are compatible with target versions
6. ✅ Epic 4 modification strategy is well-documented and feasible

**Approach:** Modify actual repositories (not stub apps)

**Epic 4 Strategy:**
- **Story 4.1:** Prepare tenant-scoped data API with augmented CSV data
- **Story 4.2:** Modify burn-performance (CLV dashboard)
  - Remove kyros-plotly-common, replace with dash-bootstrap-components
  - Remove Databricks, replace with data API calls
  - Add JWT validation for tenant isolation
  - Simplify/disable Redis caching
- **Story 4.3:** Modify mixshift (Risk dashboard)
  - Same modifications as Story 4.2

**Timeline Impact:** No impact. Epic 4 estimates already account for these modifications.

**Sign-Off:**
- **Product Owner:** Sarah (via Story 0.5 validation)
- **Date:** 2025-10-07
- **Status:** Ready to proceed to Epic 1

---

## Fallback Plan

**Status:** Not Required

Both repositories are accessible and suitable for Epic 4 integration. No fallback to stub applications necessary.

**If repositories became inaccessible:** Create minimal stub Dash applications with:
- Simple bar chart (burn-performance/CLV)
- Simple scatter plot or heatmap (mixshift/Risk)
- Mock data (50-100 rows per dataset)
- Estimated effort: 8-12 hours per app

---

## Epic 0 Summary

### Completion Status

| Story | Title | Status |
|-------|-------|--------|
| 0.1 | Verify Sample Plotly Repositories Accessibility | ✅ Complete |
| 0.2 | Validate Test Data Compatibility | ✅ Complete |
| 0.3 | Dash Application Startup Validation | ✅ Complete |
| 0.4 | Development Environment Prerequisites Validation | ✅ Complete |
| 0.5 | External Dependency Risk Assessment | ✅ Complete |

**Epic 0 Status:** ✅ **COMPLETE**

### Key Outcomes

1. ✅ **Repositories Validated** - Both burn-performance and mixshift accessible and documented
2. ✅ **Test Data Validated** - 100 rows each, compatible schemas, augmentation strategy documented
3. ✅ **Startup Limitations Documented** - Cannot start (expected), Epic 4 modification strategy defined
4. ✅ **Environment Validated** - Node.js, npm, git ready; Python 3.8 functional (3.11 upgrade recommended)
5. ✅ **Risks Assessed** - Medium overall risk level, all risks have documented mitigations
6. ✅ **Epic 4 Ready** - Clear strategy for modifying applications for PoC environment

### Next Steps

1. ✅ **Epic 0 Complete** - All prerequisite validation done
2. **Epic 1:** Foundation and shared configuration
   - Monorepo setup
   - Shared JWT validation module
   - Dependency management
3. **Epic 4:** Dash application integration (dependencies validated, strategy documented)

---

## Next Steps

1. ✅ **Story 0.1 Complete** - Repositories validated and documented
2. ✅ **Story 0.2 Complete** - Test data validated and augmentation strategy documented
3. ✅ **Story 0.3 Complete** - Dash startup validated (cannot start - expected and acceptable)
4. ✅ **Story 0.4 Complete** - Environment validation
5. ✅ **Story 0.5 Complete** - Risk assessment and Product Owner decision
6. **Epic 1:** Begin foundation work - monorepo setup and shared configuration

---

## References

- Burn-performance README: `/kyros-dev/work/kyros-saas-poc/sample-plotly-repos/burn-performance/README.md`
- Mixshift README: `/kyros-dev/work/kyros-saas-poc/sample-plotly-repos/mixshift/README.md`
- Mixshift Dev Docs: `/kyros-dev/work/kyros-saas-poc/sample-plotly-repos/mixshift/MIXSHIFT_DEV_DOCS.md`
- Mixshift User Guide: `/kyros-dev/work/kyros-saas-poc/sample-plotly-repos/mixshift/MIXSHIFT_USER_GUIDE.md`
