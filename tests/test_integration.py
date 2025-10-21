"""
Integration tests for BetFlow Engine.
"""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

class TestEndToEndWorkflow:
    """Test complete end-to-end workflows."""
    
    async def test_health_to_signals_workflow(self, client: AsyncClient, db_session: AsyncSession):
        """Test complete workflow from health check to signal generation."""
        # 1. Check system health
        health_response = await client.get("/health")
        assert health_response.status_code == 200
        health_data = health_response.json()
        assert health_data["status"] == "healthy"
        
        # 2. Test webhook ingestion
        webhook_data = {
            "provider": "test_provider",
            "data_type": "events",
            "payload": {
                "sport": "football",
                "league": "premier_league",
                "home_team": "Arsenal",
                "away_team": "Chelsea",
                "start_time": "2024-01-15T15:00:00Z",
                "status": "scheduled"
            }
        }
        
        webhook_response = await client.post("/v1/webhooks/ingest", json=webhook_data)
        assert webhook_response.status_code == 200
        webhook_result = webhook_response.json()
        assert webhook_result["status"] == "accepted"
        
        # 3. Test signal computation (internal endpoint)
        signal_response = await client.post(
            "/internal/compute_signals",
            json=["evt_test_001"]
        )
        assert signal_response.status_code == 200
        signal_result = signal_response.json()
        assert "signals_generated" in signal_result
    
    async def test_data_flow_integration(self, client: AsyncClient, db_session: AsyncSession):
        """Test data flow through the system."""
        # Mock authentication
        from api.main import app
        from api.core.security import verify_api_key
        
        async def mock_verify_api_key():
            return {"client": "test_client", "scope": "read", "api_key_id": "test_id"}
        
        app.dependency_overrides[verify_api_key] = mock_verify_api_key
        
        try:
            # 1. Ingest event data
            event_webhook = {
                "provider": "test_provider",
                "data_type": "events",
                "payload": {
                    "sport": "football",
                    "league": "premier_league",
                    "home_team": "Arsenal",
                    "away_team": "Chelsea",
                    "start_time": "2024-01-15T15:00:00Z",
                    "status": "scheduled"
                }
            }
            
            event_response = await client.post("/v1/webhooks/ingest", json=event_webhook)
            assert event_response.status_code == 200
            
            # 2. Ingest odds data
            odds_webhook = {
                "provider": "test_provider",
                "data_type": "odds",
                "payload": {
                    "event_id": "evt_test_001",
                    "book": "bet365",
                    "market": "1X2",
                    "selection": "home",
                    "price": 2.10,
                    "implied_probability": 0.476
                }
            }
            
            odds_response = await client.post("/v1/webhooks/ingest", json=odds_webhook)
            assert odds_response.status_code == 200
            
            # 3. Compute signals
            signal_response = await client.post(
                "/internal/compute_signals",
                json=["evt_test_001"]
            )
            assert signal_response.status_code == 200
            
            # 4. Query signals
            signals_response = await client.post(
                "/v1/signals/query",
                json={
                    "min_edge": 0.01,
                    "status": "active",
                    "limit": 10
                }
            )
            assert signals_response.status_code == 200
            signals_data = signals_response.json()
            assert isinstance(signals_data, list)
            
        finally:
            app.dependency_overrides.clear()
    
    async def test_error_handling_integration(self, client: AsyncClient):
        """Test error handling across the system."""
        # Test invalid webhook data
        invalid_webhook = {
            "provider": "test_provider",
            "data_type": "invalid_type",
            "payload": {}
        }
        
        response = await client.post("/v1/webhooks/ingest", json=invalid_webhook)
        assert response.status_code == 200  # Should still accept but handle gracefully
        
        # Test invalid signal computation
        invalid_signal_response = await client.post(
            "/internal/compute_signals",
            json=["non_existent_event"]
        )
        assert invalid_signal_response.status_code == 200
        result = invalid_signal_response.json()
        assert result["signals_generated"] == 0
    
    async def test_rate_limiting_integration(self, client: AsyncClient):
        """Test rate limiting across multiple requests."""
        # Make multiple requests to test rate limiting
        responses = []
        for i in range(10):
            response = await client.get("/health")
            responses.append(response)
        
        # All should succeed (health endpoint might not be rate limited)
        for response in responses:
            assert response.status_code in [200, 429]  # 429 if rate limited
    
    async def test_metrics_integration(self, client: AsyncClient):
        """Test metrics collection across the system."""
        # Make some requests to generate metrics
        await client.get("/health")
        await client.get("/metrics")
        
        # Check metrics endpoint
        metrics_response = await client.get("/metrics")
        assert metrics_response.status_code == 200
        assert "text/plain" in metrics_response.headers["content-type"]
        
        # Metrics should contain some data
        metrics_text = metrics_response.text
        assert len(metrics_text) > 0

class TestDatabaseIntegration:
    """Test database integration."""
    
    async def test_database_connection(self, db_session: AsyncSession):
        """Test database connection and basic operations."""
        from api.models.events import Event
        from api.models.odds import Odds
        from api.models.signals import Signal
        import uuid
        from datetime import datetime
        
        # Test creating and querying events
        event = Event(
            id=uuid.uuid4(),
            sport="football",
            league="premier_league",
            home_team="Arsenal",
            away_team="Chelsea",
            start_time=datetime.now(),
            status="scheduled"
        )
        
        db_session.add(event)
        await db_session.commit()
        
        # Query the event
        from sqlalchemy import select
        result = await db_session.execute(select(Event).where(Event.id == event.id))
        retrieved_event = result.scalar_one_or_none()
        
        assert retrieved_event is not None
        assert retrieved_event.sport == "football"
        assert retrieved_event.home_team == "Arsenal"
    
    async def test_database_transactions(self, db_session: AsyncSession):
        """Test database transaction handling."""
        from api.models.events import Event
        import uuid
        from datetime import datetime
        
        # Test rollback
        event = Event(
            id=uuid.uuid4(),
            sport="football",
            league="premier_league",
            home_team="Arsenal",
            away_team="Chelsea",
            start_time=datetime.now(),
            status="scheduled"
        )
        
        db_session.add(event)
        await db_session.rollback()
        
        # Event should not be persisted
        from sqlalchemy import select
        result = await db_session.execute(select(Event).where(Event.id == event.id))
        retrieved_event = result.scalar_one_or_none()
        
        assert retrieved_event is None
