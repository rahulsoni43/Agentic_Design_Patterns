"""
Base Collector Class

All collectors inherit from this base class to ensure consistent interface.
"""

from abc import ABC, abstractmethod
from typing import Optional
import logging

from ..models import CollectorResult

logger = logging.getLogger(__name__)


class BaseCollector(ABC):
    """
    Abstract base class for all data collectors

    Each collector is responsible for:
    1. Connecting to a data source
    2. Gathering relevant events
    3. Converting them to standardized Event objects
    4. Handling errors gracefully
    """

    def __init__(self, name: str):
        self.name = name
        self.logger = logging.getLogger(f"{__name__}.{name}")

    @abstractmethod
    async def collect(self, query: Optional[str] = None) -> CollectorResult:
        """
        Collect data from the source

        Args:
            query: Optional query context (e.g., "api-server pods")

        Returns:
            CollectorResult with events and metadata

        Raises:
            Should NOT raise - catch all exceptions and return error in result
        """
        pass

    async def health_check(self) -> bool:
        """
        Check if the collector can reach its data source

        Returns:
            True if healthy, False otherwise
        """
        try:
            result = await self.collect()
            return result.success
        except Exception as e:
            self.logger.error(f"Health check failed: {e}")
            return False
