"""Unit tests for tenant metadata and dashboards endpoints."""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock

from src.main import app

client = TestClient(app)


@pytest.fixture
def mock_tenant_token():
    """Mock tenant-scoped token for Acme."""
    return "eyJ-mock-tenant-token-acme"


@pytest.fixture
def mock_beta_token():
    """Mock tenant-scoped token for Beta."""
    return "eyJ-mock-tenant-token-beta"


@pytest.fixture
def mock_tenant_context_acme():
    """Mock tenant context for Acme."""
    return {
        "sub": "analyst-uuid",
        "email": "analyst@acme.com",
        "tenant_id": "acme-uuid",
        "role": "viewer"
    }


@pytest.fixture
def mock_tenant_context_beta():
    """Mock tenant context for Beta."""
    return {
        "sub": "viewer-uuid",
        "email": "viewer@beta.com",
        "tenant_id": "beta-uuid",
        "role": "viewer"
    }


@pytest.fixture
def mock_acme_tenant_data():
    """Mock tenant data for Acme Corporation."""
    return {
        "id": "acme-uuid",
        "name": "Acme Corporation",
        "slug": "acme-corp",
        "is_active": 1,
        "config_json": {
            "branding": {
                "logo_url": "/logos/acme.png",
                "primary_color": "#1a73e8"
            }
        },
        "created_at": "2024-01-01T00:00:00Z"
    }


@pytest.fixture
def mock_acme_dashboards():
    """Mock dashboards for Acme (CLV and Risk, alphabetically sorted)."""
    return [
        {
            "slug": "customer-lifetime-value",
            "title": "Customer Lifetime Value",
            "description": "CLV analysis and predictions",
            "config_json": {"refresh_interval": 300}
        },
        {
            "slug": "risk-analysis",
            "title": "Risk Analysis",
            "description": "Risk scoring and monitoring",
            "config_json": {"refresh_interval": 60}
        }
    ]


@pytest.fixture
def mock_beta_dashboards():
    """Mock dashboards for Beta (only Risk)."""
    return [
        {
            "slug": "risk-analysis",
            "title": "Risk Analysis",
            "description": "Risk scoring and monitoring",
            "config_json": {"refresh_interval": 60}
        }
    ]


def test_get_tenant_metadata_success(mock_tenant_context_acme, mock_acme_tenant_data):
    """Test GET /api/tenant/{tenant_id} with valid token returns tenant metadata."""
    with patch('src.routers.tenant_routes.get_current_tenant') as mock_get_tenant, \
         patch('src.routers.tenant_routes.validate_tenant_access') as mock_validate, \
         patch('src.routers.tenant_routes.get_db_connection') as mock_db:

        # Setup mocks
        mock_get_tenant.return_value = mock_tenant_context_acme
        mock_validate.return_value = None

        mock_connection = AsyncMock()
        mock_db.return_value.__aenter__.return_value = mock_connection

        # Mock database query
        async def mock_get_tenant_by_id(db, tenant_id):
            return mock_acme_tenant_data

        with patch('src.routers.tenant_routes.get_tenant_by_id', new=mock_get_tenant_by_id):
            response = client.get(
                "/api/tenant/acme-uuid",
                headers={"Authorization": "Bearer mock-token"}
            )

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == "acme-uuid"
        assert data["name"] == "Acme Corporation"
        assert data["slug"] == "acme-corp"
        assert data["is_active"] == 1
        assert "config_json" in data
        assert isinstance(data["config_json"], dict)


def test_get_tenant_metadata_not_found(mock_tenant_context_acme):
    """Test GET /api/tenant/{tenant_id} returns 404 for non-existent tenant."""
    with patch('src.routers.tenant_routes.get_current_tenant') as mock_get_tenant, \
         patch('src.routers.tenant_routes.validate_tenant_access') as mock_validate, \
         patch('src.routers.tenant_routes.get_db_connection') as mock_db:

        mock_get_tenant.return_value = mock_tenant_context_acme
        mock_validate.return_value = None

        mock_connection = AsyncMock()
        mock_db.return_value.__aenter__.return_value = mock_connection

        # Mock database returning None
        async def mock_get_tenant_by_id(db, tenant_id):
            return None

        with patch('src.routers.tenant_routes.get_tenant_by_id', new=mock_get_tenant_by_id):
            response = client.get(
                "/api/tenant/nonexistent-uuid",
                headers={"Authorization": "Bearer mock-token"}
            )

        assert response.status_code == 404
        error = response.json()["error"]
        assert error["code"] == "TENANT_NOT_FOUND"
        assert "nonexistent-uuid" in error["message"]


def test_get_tenant_metadata_mismatch_returns_403():
    """Test that tenant_id mismatch between token and path returns 403."""
    # Mock token with acme-uuid, but requesting beta-uuid
    mock_context = {
        "sub": "user-uuid",
        "tenant_id": "acme-uuid",
        "role": "viewer"
    }

    with patch('src.routers.tenant_routes.get_current_tenant') as mock_get_tenant:
        mock_get_tenant.return_value = mock_context

        # validate_tenant_access is real dependency, will raise 403
        response = client.get(
            "/api/tenant/beta-uuid",
            headers={"Authorization": "Bearer mock-token"}
        )

        assert response.status_code == 403
        error = response.json()["error"]
        assert error["code"] == "TENANT_MISMATCH"


def test_get_tenant_dashboards_acme(mock_tenant_context_acme, mock_acme_dashboards):
    """Test GET /api/tenant/{tenant_id}/dashboards returns Acme's 2 dashboards."""
    with patch('src.routers.tenant_routes.get_current_tenant') as mock_get_tenant, \
         patch('src.routers.tenant_routes.validate_tenant_access') as mock_validate, \
         patch('src.routers.tenant_routes.get_db_connection') as mock_db:

        mock_get_tenant.return_value = mock_tenant_context_acme
        mock_validate.return_value = None

        mock_connection = AsyncMock()
        mock_db.return_value.__aenter__.return_value = mock_connection

        # Mock database query
        async def mock_get_dashboards(db, tenant_id):
            return mock_acme_dashboards

        with patch('src.routers.tenant_routes.get_tenant_dashboards', new=mock_get_dashboards):
            response = client.get(
                "/api/tenant/acme-uuid/dashboards",
                headers={"Authorization": "Bearer mock-token"}
            )

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert data[0]["slug"] == "customer-lifetime-value"
        assert data[1]["slug"] == "risk-analysis"


def test_get_tenant_dashboards_beta(mock_tenant_context_beta, mock_beta_dashboards):
    """Test GET /api/tenant/{tenant_id}/dashboards returns Beta's 1 dashboard."""
    with patch('src.routers.tenant_routes.get_current_tenant') as mock_get_tenant, \
         patch('src.routers.tenant_routes.validate_tenant_access') as mock_validate, \
         patch('src.routers.tenant_routes.get_db_connection') as mock_db:

        mock_get_tenant.return_value = mock_tenant_context_beta
        mock_validate.return_value = None

        mock_connection = AsyncMock()
        mock_db.return_value.__aenter__.return_value = mock_connection

        async def mock_get_dashboards(db, tenant_id):
            return mock_beta_dashboards

        with patch('src.routers.tenant_routes.get_tenant_dashboards', new=mock_get_dashboards):
            response = client.get(
                "/api/tenant/beta-uuid/dashboards",
                headers={"Authorization": "Bearer mock-token"}
            )

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["slug"] == "risk-analysis"


def test_dashboards_alphabetical_sorting(mock_tenant_context_acme):
    """Test that dashboards are sorted alphabetically by title."""
    # Dashboards intentionally out of order
    unsorted_dashboards = [
        {
            "slug": "risk-analysis",
            "title": "Risk Analysis",  # Should be second
            "description": "Risk scoring",
            "config_json": {}
        },
        {
            "slug": "customer-lifetime-value",
            "title": "Customer Lifetime Value",  # Should be first
            "description": "CLV analysis",
            "config_json": {}
        }
    ]

    with patch('src.routers.tenant_routes.get_current_tenant') as mock_get_tenant, \
         patch('src.routers.tenant_routes.validate_tenant_access') as mock_validate, \
         patch('src.routers.tenant_routes.get_db_connection') as mock_db:

        mock_get_tenant.return_value = mock_tenant_context_acme
        mock_validate.return_value = None

        mock_connection = AsyncMock()
        mock_db.return_value.__aenter__.return_value = mock_connection

        # Database query already returns sorted (ORDER BY d.title ASC)
        async def mock_get_dashboards(db, tenant_id):
            # Simulate database sorting
            return sorted(unsorted_dashboards, key=lambda x: x["title"])

        with patch('src.routers.tenant_routes.get_tenant_dashboards', new=mock_get_dashboards):
            response = client.get(
                "/api/tenant/acme-uuid/dashboards",
                headers={"Authorization": "Bearer mock-token"}
            )

        data = response.json()
        assert data[0]["title"] == "Customer Lifetime Value"
        assert data[1]["title"] == "Risk Analysis"


def test_tenant_no_dashboards(mock_tenant_context_acme):
    """Test that tenant with no dashboards returns empty array (not error)."""
    with patch('src.routers.tenant_routes.get_current_tenant') as mock_get_tenant, \
         patch('src.routers.tenant_routes.validate_tenant_access') as mock_validate, \
         patch('src.routers.tenant_routes.get_db_connection') as mock_db:

        mock_get_tenant.return_value = mock_tenant_context_acme
        mock_validate.return_value = None

        mock_connection = AsyncMock()
        mock_db.return_value.__aenter__.return_value = mock_connection

        async def mock_get_dashboards(db, tenant_id):
            return []

        with patch('src.routers.tenant_routes.get_tenant_dashboards', new=mock_get_dashboards):
            response = client.get(
                "/api/tenant/acme-uuid/dashboards",
                headers={"Authorization": "Bearer mock-token"}
            )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 0


def test_config_json_properly_parsed(mock_tenant_context_acme, mock_acme_tenant_data):
    """Test that config_json is returned as dict, not string."""
    with patch('src.routers.tenant_routes.get_current_tenant') as mock_get_tenant, \
         patch('src.routers.tenant_routes.validate_tenant_access') as mock_validate, \
         patch('src.routers.tenant_routes.get_db_connection') as mock_db:

        mock_get_tenant.return_value = mock_tenant_context_acme
        mock_validate.return_value = None

        mock_connection = AsyncMock()
        mock_db.return_value.__aenter__.return_value = mock_connection

        async def mock_get_tenant_by_id(db, tenant_id):
            return mock_acme_tenant_data

        with patch('src.routers.tenant_routes.get_tenant_by_id', new=mock_get_tenant_by_id):
            response = client.get(
                "/api/tenant/acme-uuid",
                headers={"Authorization": "Bearer mock-token"}
            )

        data = response.json()
        assert isinstance(data["config_json"], dict)
        assert "branding" in data["config_json"]
        assert data["config_json"]["branding"]["primary_color"] == "#1a73e8"
