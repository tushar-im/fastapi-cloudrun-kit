import pytest
from httpx import AsyncClient


class TestMainEndpoints:
    """Test main application endpoints."""

    async def test_root_endpoint(self, client: AsyncClient):
        """Test root endpoint."""
        response = await client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "version" in data
        assert "FastAPI CloudRun Kit" in data["message"]

    async def test_health_check(self, client: AsyncClient):
        """Test health check endpoint."""
        response = await client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data
        assert "app_name" in data
        assert "version" in data
        assert "environment" in data

    async def test_readiness_check(self, client: AsyncClient):
        """Test readiness check endpoint."""
        response = await client.get("/ready")
        # Status code could be 200 or 503 depending on Firebase connection
        assert response.status_code in [200, 503]
        data = response.json()
        assert "status" in data
        assert "timestamp" in data
        assert "checks" in data
        assert "firebase" in data["checks"]

    @pytest.mark.skipif(True, reason="Only available in development")
    async def test_debug_config_endpoint(self, client: AsyncClient):
        """Test debug config endpoint (development only)."""
        response = await client.get("/debug/config")
        # This endpoint is only available in non-production environments
        if response.status_code == 200:
            data = response.json()
            assert "config" in data
            assert "firebase_emulator_config" in data
            assert "should_use_emulator" in data

    async def test_nonexistent_endpoint(self, client: AsyncClient):
        """Test non-existent endpoint returns 404."""
        response = await client.get("/nonexistent")
        assert response.status_code == 404
