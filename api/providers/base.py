"""
Base provider interface for data sources.
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from datetime import date
from ..models.schemas import EventResponse, OddsResponse

class OddsProvider(ABC):
    """Base interface for odds data providers."""
    
    @abstractmethod
    async def fetch_events(self, sport: Optional[str] = None,
                          date_from: Optional[date] = None,
                          date_to: Optional[date] = None,
                          league: Optional[str] = None) -> List[EventResponse]:
        """Fetch events from provider."""
        pass
    
    @abstractmethod
    async def fetch_odds(self, event_ids: List[str],
                        market: Optional[str] = None) -> List[OddsResponse]:
        """Fetch odds for events from provider."""
        pass
    
    @abstractmethod
    async def health_check(self) -> bool:
        """Check if provider is healthy."""
        pass
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Provider name."""
        pass
    
    @property
    @abstractmethod
    def is_configured(self) -> bool:
        """Check if provider is properly configured."""
        pass
