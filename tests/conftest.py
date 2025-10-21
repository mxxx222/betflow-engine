"""
Pytest configuration and fixtures for BetFlow Engine tests.
"""

import pytest
import asyncio
from typing import AsyncGenerator
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import StaticPool

from api.main import app
from api.core.database import get_db, Base
from api.core.config import settings

# Test database URL
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

# Create test engine
test_engine = create_async_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

TestSessionLocal = async_sessionmaker(
    test_engine,
    class_=AsyncSession,
    expire_on_commit=False
)

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="function")
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """Create a test database session."""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    async with TestSessionLocal() as session:
        yield session
        await session.rollback()
    
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

@pytest.fixture(scope="function")
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """Create a test client."""
    def override_get_db():
        return db_session
    
    app.dependency_overrides[get_db] = override_get_db
    
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac
    
    app.dependency_overrides.clear()

@pytest.fixture
def sample_event_data():
    """Sample event data for testing."""
    return {
        "id": "evt_test_001",
        "sport": "football",
        "league": "premier_league",
        "home_team": "Arsenal",
        "away_team": "Chelsea",
        "start_time": "2024-01-15T15:00:00Z",
        "status": "scheduled",
        "venue": "Emirates Stadium"
    }

@pytest.fixture
def sample_odds_data():
    """Sample odds data for testing."""
    return {
        "id": "odds_test_001",
        "event_id": "evt_test_001",
        "book": "bet365",
        "market": "1X2",
        "selection": "home",
        "price": 2.10,
        "implied_probability": 0.476,
        "fetched_at": "2024-01-01T12:00:00Z"
    }

@pytest.fixture
def sample_signal_data():
    """Sample signal data for testing."""
    return {
        "id": "sig_test_001",
        "event_id": "evt_test_001",
        "market": "1X2",
        "signal_type": "edge",
        "implied_probability": 0.476,
        "fair_odds": 2.20,
        "best_book_odds": 2.10,
        "edge": 0.047,
        "confidence": 0.75,
        "risk_note": "Educational analytics only",
        "explanation": "Fair probability: 0.455, Edge: 0.047",
        "status": "active"
    }

@pytest.fixture
def api_key_headers():
    """API key headers for authentication."""
    return {
        "Authorization": "Bearer test-api-key"
    }
