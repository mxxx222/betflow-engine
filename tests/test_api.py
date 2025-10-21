"""
API endpoint tests for BetFlow Engine.
"""

import pytest
from httpx import AsyncClient
from fastapi import status

class TestHealthEndpoint:
    """Test health check endpoint."""
    
    async def test_health_check(self, client: AsyncClient):
        """Test health check endpoint returns 200."""
        response = await client.get("/health")
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data
        assert "version" in data
        assert "services" in data

class TestEventsEndpoint:
    """Test events endpoint."""
    
    async def test_get_events_without_auth(self, client: AsyncClient):
        """Test events endpoint requires authentication."""
        response = await client.get("/v1/events")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    async def test_get_events_with_auth(self, client: AsyncClient, api_key_headers):
        """Test events endpoint with authentication."""
        # Mock the authentication dependency
        from api.main import app
        from api.core.security import verify_api_key
        
        async def mock_verify_api_key():
            return {"client": "test_client", "scope": "read", "api_key_id": "test_id"}
        
        app.dependency_overrides[verify_api_key] = mock_verify_api_key
        
        response = await client.get("/v1/events", headers=api_key_headers)
        # Should return 200 even if no events (empty list)
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        assert isinstance(data, list)
        
        app.dependency_overrides.clear()

class TestOddsEndpoint:
    """Test odds endpoint."""
    
    async def test_get_odds_without_auth(self, client: AsyncClient):
        """Test odds endpoint requires authentication."""
        response = await client.get("/v1/odds?event_id=test")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    async def test_get_odds_with_auth(self, client: AsyncClient, api_key_headers):
        """Test odds endpoint with authentication."""
        from api.main import app
        from api.core.security import verify_api_key
        
        async def mock_verify_api_key():
            return {"client": "test_client", "scope": "read", "api_key_id": "test_id"}
        
        app.dependency_overrides[verify_api_key] = mock_verify_api_key
        
        response = await client.get("/v1/odds?event_id=test", headers=api_key_headers)
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        assert isinstance(data, list)
        
        app.dependency_overrides.clear()

class TestSignalsEndpoint:
    """Test signals endpoint."""
    
    async def test_query_signals_without_auth(self, client: AsyncClient):
        """Test signals query requires authentication."""
        response = await client.post("/v1/signals/query", json={})
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    async def test_query_signals_with_auth(self, client: AsyncClient, api_key_headers):
        """Test signals query with authentication."""
        from api.main import app
        from api.core.security import verify_api_key
        
        async def mock_verify_api_key():
            return {"client": "test_client", "scope": "read", "api_key_id": "test_id"}
        
        app.dependency_overrides[verify_api_key] = mock_verify_api_key
        
        query_data = {
            "min_edge": 0.05,
            "status": "active",
            "limit": 10
        }
        
        response = await client.post("/v1/signals/query", json=query_data, headers=api_key_headers)
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        assert isinstance(data, list)
        
        app.dependency_overrides.clear()
    
    async def test_get_signal_by_id(self, client: AsyncClient, api_key_headers):
        """Test get specific signal by ID."""
        from api.main import app
        from api.core.security import verify_api_key
        
        async def mock_verify_api_key():
            return {"client": "test_client", "scope": "read", "api_key_id": "test_id"}
        
        app.dependency_overrides[verify_api_key] = mock_verify_api_key
        
        response = await client.get("/v1/signals/non-existent-id", headers=api_key_headers)
        assert response.status_code == status.HTTP_404_NOT_FOUND
        
        app.dependency_overrides.clear()

class TestWebhookEndpoint:
    """Test webhook endpoint."""
    
    async def test_webhook_ingest(self, client: AsyncClient):
        """Test webhook data ingestion."""
        webhook_data = {
            "provider": "test_provider",
            "data_type": "events",
            "payload": {
                "event_id": "evt_test_001",
                "sport": "football",
                "home_team": "Arsenal",
                "away_team": "Chelsea"
            }
        }
        
        response = await client.post("/v1/webhooks/ingest", json=webhook_data)
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        assert data["status"] == "accepted"
        assert "message" in data

class TestModelStatusEndpoint:
    """Test model status endpoint."""
    
    async def test_model_status_without_auth(self, client: AsyncClient):
        """Test model status requires authentication."""
        response = await client.get("/v1/models/status")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    async def test_model_status_with_auth(self, client: AsyncClient, api_key_headers):
        """Test model status with authentication."""
        from api.main import app
        from api.core.security import verify_api_key
        
        async def mock_verify_api_key():
            return {"client": "test_client", "scope": "read", "api_key_id": "test_id"}
        
        app.dependency_overrides[verify_api_key] = mock_verify_api_key
        
        response = await client.get("/v1/models/status", headers=api_key_headers)
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        assert "models" in data
        assert "total_signals" in data
        assert "active_signals" in data
        
        app.dependency_overrides.clear()

class TestMetricsEndpoint:
    """Test metrics endpoint."""
    
    async def test_metrics_endpoint(self, client: AsyncClient):
        """Test Prometheus metrics endpoint."""
        response = await client.get("/metrics")
        assert response.status_code == status.HTTP_200_OK
        assert "text/plain" in response.headers["content-type"]

class TestErrorHandling:
    """Test error handling."""
    
    async def test_404_endpoint(self, client: AsyncClient):
        """Test 404 for non-existent endpoint."""
        response = await client.get("/non-existent")
        assert response.status_code == status.HTTP_404_NOT_FOUND
    
    async def test_invalid_json(self, client: AsyncClient):
        """Test invalid JSON handling."""
        response = await client.post(
            "/v1/signals/query",
            data="invalid json",
            headers={"Content-Type": "application/json"}
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
