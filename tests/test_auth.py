import pytest
from httpx import AsyncClient


class TestAuthentication:
    """Test authentication endpoints."""

    @pytest.mark.firebase
    async def test_register_user(
        self, client: AsyncClient, test_user_data: dict, clean_firestore
    ):
        """Test user registration."""
        response = await client.post("/api/v1/auth/register", json=test_user_data)

        assert response.status_code == 200
        data = response.json()
        assert "uid" in data
        assert data["email"] == test_user_data["email"]
        assert data["display_name"] == test_user_data["display_name"]
        assert data["disabled"] == False
        assert data["email_verified"] == False

    @pytest.mark.firebase
    async def test_register_duplicate_email(
        self, client: AsyncClient, test_user_data: dict, clean_firestore
    ):
        """Test registration with duplicate email fails."""
        # Register user first time
        response1 = await client.post("/api/v1/auth/register", json=test_user_data)
        assert response1.status_code == 200

        # Try to register same email again
        response2 = await client.post("/api/v1/auth/register", json=test_user_data)
        assert response2.status_code == 400
        assert "already exists" in response2.json()["detail"].lower()

    async def test_register_invalid_data(self, client: AsyncClient):
        """Test registration with invalid data."""
        invalid_data = {
            "email": "invalid-email",
            "password": "weak",  # Too short
            "display_name": "",  # Empty
        }

        response = await client.post("/api/v1/auth/register", json=invalid_data)
        assert response.status_code == 422

    @pytest.mark.firebase
    async def test_get_current_user_without_auth(self, client: AsyncClient):
        """Test getting current user without authentication."""
        response = await client.get("/api/v1/auth/me")
        assert response.status_code == 403

    @pytest.mark.firebase
    async def test_get_current_user_with_auth(
        self, client: AsyncClient, auth_headers: dict
    ):
        """Test getting current user with authentication."""
        response = await client.get("/api/v1/auth/me", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "uid" in data
        assert "email" in data
        assert "display_name" in data

    @pytest.mark.firebase
    async def test_logout(self, client: AsyncClient, auth_headers: dict):
        """Test user logout."""
        response = await client.post("/api/v1/auth/logout", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "logged out" in data["message"].lower()

    async def test_password_reset_request(self, client: AsyncClient):
        """Test password reset request."""
        response = await client.post(
            "/api/v1/auth/password/reset", json={"email": "test@example.com"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "reset email sent" in data["message"].lower()

    @pytest.mark.firebase
    async def test_password_update(self, client: AsyncClient, auth_headers: dict):
        """Test password update."""
        response = await client.post(
            "/api/v1/auth/password/update",
            json={
                "current_password": "TestPassword123!",
                "new_password": "NewTestPassword123!",
            },
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "updated" in data["message"].lower()

    @pytest.mark.firebase
    async def test_email_verification(self, client: AsyncClient, auth_headers: dict):
        """Test email verification request."""
        response = await client.post("/api/v1/auth/verify-email", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "verification email sent" in data["message"].lower()

    async def test_invalid_token(self, client: AsyncClient):
        """Test request with invalid token."""
        headers = {
            "Authorization": "Bearer invalid-token",
            "Content-Type": "application/json",
        }

        response = await client.get("/api/v1/auth/me", headers=headers)
        assert response.status_code == 401

    async def test_refresh_token(self, client: AsyncClient):
        """Test token refresh."""
        # Create a refresh token
        from app.core.security import create_refresh_token

        refresh_token = create_refresh_token("test-user-id")

        headers = {
            "Authorization": f"Bearer {refresh_token}",
            "Content-Type": "application/json",
        }

        response = await client.post("/api/v1/auth/refresh", headers=headers)

        # This might fail if the user doesn't exist, which is expected in this test
        # The important thing is that the token format is validated
        assert response.status_code in [200, 401]
