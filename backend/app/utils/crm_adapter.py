"""
CRM Adapter Interface
Abstract interface for CRM integration - ready for implementation
"""
import logging
from abc import ABC, abstractmethod
from typing import Dict, Optional, List
from datetime import datetime

logger = logging.getLogger(__name__)


class CRMAdapter(ABC):
    """
    Abstract base class for CRM adapters
    This allows the system to work with different CRM systems
    """
    
    @abstractmethod
    async def get_client_info(self, client_id: str) -> Optional[Dict]:
        """
        Get client information from CRM
        
        Returns:
            {
                "client_id": str,
                "child_name": Optional[str],
                "parent_name": Optional[str],
                "trainer_name": Optional[str],
                "schedule": Optional[Dict],
                "course": Optional[str],
            }
        """
        pass
    
    @abstractmethod
    async def get_schedule(self, client_id: str) -> Optional[List[Dict]]:
        """
        Get schedule for client
        
        Returns:
            List of schedule items with datetime, trainer, subject
        """
        pass
    
    @abstractmethod
    async def mark_absence(self, client_id: str, date: datetime, reason: str) -> bool:
        """
        Mark absence in CRM
        
        Returns:
            True if successful
        """
        pass
    
    @abstractmethod
    async def get_referral_link(self, client_id: str) -> str:
        """
        Get referral link for client
        
        Returns:
            Referral link URL
        """
        pass


class MockCRMAdapter(CRMAdapter):
    """
    Mock CRM adapter for testing and development
    Can be replaced with real CRM adapter when integration is ready
    """
    
    async def get_client_info(self, client_id: str) -> Optional[Dict]:
        """Mock implementation"""
        # In real implementation, this would call CRM API
        return {
            "client_id": client_id,
            "child_name": None,  # Will be extracted from message if not available
            "parent_name": None,
            "trainer_name": None,
            "schedule": None,
            "course": None,
        }
    
    async def get_schedule(self, client_id: str) -> Optional[List[Dict]]:
        """Mock implementation"""
        return None
    
    async def mark_absence(self, client_id: str, date: datetime, reason: str) -> bool:
        """Mock implementation"""
        logger.info(f"Mock: Marking absence for {client_id} on {date}")
        return True
    
    async def get_referral_link(self, client_id: str) -> str:
        """Mock implementation"""
        return f"https://example.com/ref/{client_id}"


# Global CRM adapter instance (will be set during initialization)
_crm_adapter: Optional[CRMAdapter] = None


def get_crm_adapter() -> CRMAdapter:
    """Get current CRM adapter instance"""
    global _crm_adapter
    if _crm_adapter is None:
        _crm_adapter = MockCRMAdapter()
        logger.info("Using MockCRMAdapter (no real CRM integration)")
    return _crm_adapter


def set_crm_adapter(adapter: CRMAdapter):
    """Set CRM adapter instance"""
    global _crm_adapter
    _crm_adapter = adapter
    logger.info(f"CRM adapter set to {type(adapter).__name__}")







