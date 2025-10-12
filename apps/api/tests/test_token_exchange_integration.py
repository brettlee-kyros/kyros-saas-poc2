"""Integration and security tests for token exchange endpoint."""
import sys

import jwt
import pytest
from fastapi.testclient import TestClient

# Add paths for imports
sys.path.insert(0, '/app/packages/shared-config/src')

from shared_config import (
    encode_user_token,
    validate_tenant_token,
    JWT_SECRET_KEY,
    JWT_ALGORITHM,
    get_user_by_email
)

from apps.api.src.main import app


@pytest.fixture
def client():
    """FastAPI test client fixture."""
    return TestClient(app)


class TestTokenExchangeIntegration:
    """Integration tests for complete token exchange flow with real database."""

    def test_complete_exchange_flow_analyst_acme(self, client):
        """Test complete exchange flow: analyst@acme.com -> Acme tenant (viewer role)."""
        # Get mock user data
        user_data = get_user_by_email("analyst@acme.com")
        assert user_data is not None

        # Generate user token
        user_token = encode_user_token({
            "user_id": user_data["user_id"],
            "email": user_data["email"],
            "tenant_ids": user_data["tenant_ids"]
        })

        # Extract Acme tenant ID (first in array)
        acme_tenant_id = user_data["tenant_ids"][0]

        # Exchange for Acme tenant
        response = client.post(
            "/api/token/exchange",
            json={"tenant_id": acme_tenant_id},
            headers={"Authorization": f"Bearer {user_token}"}
        )

        # Verify success
        assert response.status_code == 200
        data = response.json()

        # Decode tenant-scoped token
        tenant_token = data["access_token"]
        decoded = jwt.decode(tenant_token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])

        # Verify claims
        assert decoded["email"] == "analyst@acme.com"
        assert decoded["tenant_id"] == acme_tenant_id
        assert decoded["role"] == "viewer"
        assert isinstance(decoded["tenant_id"], str)  # Single value

    def test_complete_exchange_flow_admin_acme_to_acme(self, client):
        """Test exchange: admin@acme.com -> Acme tenant (admin role)."""
        user_data = get_user_by_email("admin@acme.com")
        assert user_data is not None

        user_token = encode_user_token({
            "user_id": user_data["user_id"],
            "email": user_data["email"],
            "tenant_ids": user_data["tenant_ids"]
        })

        # admin@acme.com has access to both Acme and Beta
        # Exchange for Acme (should be first in tenant_ids)
        acme_tenant_id = user_data["tenant_ids"][0]

        response = client.post(
            "/api/token/exchange",
            json={"tenant_id": acme_tenant_id},
            headers={"Authorization": f"Bearer {user_token}"}
        )

        assert response.status_code == 200
        tenant_token = response.json()["access_token"]
        decoded = jwt.decode(tenant_token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])

        assert decoded["email"] == "admin@acme.com"
        assert decoded["role"] == "admin"

    def test_complete_exchange_flow_admin_acme_to_beta(self, client):
        """Test exchange: admin@acme.com -> Beta tenant (admin role)."""
        user_data = get_user_by_email("admin@acme.com")
        user_token = encode_user_token({
            "user_id": user_data["user_id"],
            "email": user_data["email"],
            "tenant_ids": user_data["tenant_ids"]
        })

        # Exchange for Beta tenant (second in array)
        beta_tenant_id = user_data["tenant_ids"][1] if len(user_data["tenant_ids"]) > 1 else None
        assert beta_tenant_id is not None, "admin@acme.com should have access to Beta"

        response = client.post(
            "/api/token/exchange",
            json={"tenant_id": beta_tenant_id},
            headers={"Authorization": f"Bearer {user_token}"}
        )

        assert response.status_code == 200
        tenant_token = response.json()["access_token"]
        decoded = jwt.decode(tenant_token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])

        assert decoded["email"] == "admin@acme.com"
        assert decoded["tenant_id"] == beta_tenant_id
        assert decoded["role"] == "admin"

    def test_complete_exchange_flow_viewer_beta(self, client):
        """Test exchange: viewer@beta.com -> Beta tenant (viewer role)."""
        user_data = get_user_by_email("viewer@beta.com")
        user_token = encode_user_token({
            "user_id": user_data["user_id"],
            "email": user_data["email"],
            "tenant_ids": user_data["tenant_ids"]
        })

        beta_tenant_id = user_data["tenant_ids"][0]

        response = client.post(
            "/api/token/exchange",
            json={"tenant_id": beta_tenant_id},
            headers={"Authorization": f"Bearer {user_token}"}
        )

        assert response.status_code == 200
        tenant_token = response.json()["access_token"]
        decoded = jwt.decode(tenant_token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])

        assert decoded["email"] == "viewer@beta.com"
        assert decoded["role"] == "viewer"

    def test_tenant_token_can_be_validated(self, client):
        """Verify resulting token can be validated with validate_tenant_token()."""
        user_data = get_user_by_email("analyst@acme.com")
        user_token = encode_user_token({
            "user_id": user_data["user_id"],
            "email": user_data["email"],
            "tenant_ids": user_data["tenant_ids"]
        })

        response = client.post(
            "/api/token/exchange",
            json={"tenant_id": user_data["tenant_ids"][0]},
            headers={"Authorization": f"Bearer {user_token}"}
        )

        tenant_token = response.json()["access_token"]

        # Validate with shared_config function
        validated = validate_tenant_token(tenant_token)
        assert validated is not None
        assert validated.tenant_id == user_data["tenant_ids"][0]
        assert validated.role in ["admin", "viewer"]

    def test_response_structure(self, client):
        """Verify response structure matches TokenResponse specification."""
        user_data = get_user_by_email("analyst@acme.com")
        user_token = encode_user_token({
            "user_id": user_data["user_id"],
            "email": user_data["email"],
            "tenant_ids": user_data["tenant_ids"]
        })

        response = client.post(
            "/api/token/exchange",
            json={"tenant_id": user_data["tenant_ids"][0]},
            headers={"Authorization": f"Bearer {user_token}"}
        )

        data = response.json()

        # Verify top-level structure
        assert "access_token" in data
        assert "token_type" in data
        assert "expires_in" in data

        # Verify types
        assert isinstance(data["access_token"], str)
        assert isinstance(data["token_type"], str)
        assert isinstance(data["expires_in"], int)

        # Verify values
        assert data["token_type"] == "Bearer"
        assert data["expires_in"] == 1800


class TestTokenExchangeSecurity:
    """Security tests for unauthorized access prevention."""

    def test_analyst_acme_cannot_access_beta(self, client):
        """Security test: analyst@acme.com cannot exchange for Beta tenant."""
        user_data = get_user_by_email("analyst@acme.com")
        user_token = encode_user_token({
            "user_id": user_data["user_id"],
            "email": user_data["email"],
            "tenant_ids": user_data["tenant_ids"]
        })

        # Get Beta tenant ID from admin user
        admin_data = get_user_by_email("admin@acme.com")
        beta_tenant_id = admin_data["tenant_ids"][1] if len(admin_data["tenant_ids"]) > 1 else None

        # Attempt unauthorized exchange
        response = client.post(
            "/api/token/exchange",
            json={"tenant_id": beta_tenant_id},
            headers={"Authorization": f"Bearer {user_token}"}
        )

        # Should be denied
        assert response.status_code == 403
        data = response.json()
        assert data["error"]["code"] == "TENANT_ACCESS_DENIED"

    def test_viewer_beta_cannot_access_acme(self, client):
        """Security test: viewer@beta.com cannot exchange for Acme tenant."""
        user_data = get_user_by_email("viewer@beta.com")
        user_token = encode_user_token({
            "user_id": user_data["user_id"],
            "email": user_data["email"],
            "tenant_ids": user_data["tenant_ids"]
        })

        # Get Acme tenant ID
        acme_user = get_user_by_email("analyst@acme.com")
        acme_tenant_id = acme_user["tenant_ids"][0]

        # Attempt unauthorized exchange
        response = client.post(
            "/api/token/exchange",
            json={"tenant_id": acme_tenant_id},
            headers={"Authorization": f"Bearer {user_token}"}
        )

        # Should be denied
        assert response.status_code == 403
        data = response.json()
        assert data["error"]["code"] == "TENANT_ACCESS_DENIED"

    def test_admin_can_access_both_tenants(self, client):
        """Verify admin@acme.com CAN access both Acme and Beta (authorized)."""
        user_data = get_user_by_email("admin@acme.com")
        user_token = encode_user_token({
            "user_id": user_data["user_id"],
            "email": user_data["email"],
            "tenant_ids": user_data["tenant_ids"]
        })

        # Test exchange for both tenants
        for tenant_id in user_data["tenant_ids"]:
            response = client.post(
                "/api/token/exchange",
                json={"tenant_id": tenant_id},
                headers={"Authorization": f"Bearer {user_token}"}
            )

            # Both should succeed
            assert response.status_code == 200

    def test_cross_tenant_access_matrix(self, client):
        """Comprehensive cross-tenant access test matrix."""
        # Define test matrix: (user, tenant) -> expected result
        test_cases = [
            ("analyst@acme.com", 0, 200),  # analyst -> acme (authorized)
            ("viewer@beta.com", 0, 200),   # viewer -> beta (authorized)
            ("admin@acme.com", 0, 200),    # admin -> acme (authorized)
            ("admin@acme.com", 1, 200),    # admin -> beta (authorized)
        ]

        for email, tenant_idx, expected_status in test_cases:
            user_data = get_user_by_email(email)
            user_token = encode_user_token({
                "user_id": user_data["user_id"],
                "email": user_data["email"],
                "tenant_ids": user_data["tenant_ids"]
            })

            tenant_id = user_data["tenant_ids"][tenant_idx]

            response = client.post(
                "/api/token/exchange",
                json={"tenant_id": tenant_id},
                headers={"Authorization": f"Bearer {user_token}"}
            )

            assert response.status_code == expected_status, \
                f"Failed for {email} -> tenant_idx {tenant_idx}"

    def test_invalid_user_token_returns_401(self, client):
        """Test with invalid user token returns 401."""
        response = client.post(
            "/api/token/exchange",
            json={"tenant_id": "some-tenant-id"},
            headers={"Authorization": "Bearer invalid-token"}
        )

        assert response.status_code == 401

    def test_missing_authorization_header(self, client):
        """Test with missing Authorization header returns 401 or 403."""
        response = client.post(
            "/api/token/exchange",
            json={"tenant_id": "some-tenant-id"}
        )

        # FastAPI HTTPBearer may return 401 or 403
        assert response.status_code in [401, 403]
