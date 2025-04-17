import logging
import uuid
from typing import Dict, List, Optional, Any

from app.core.supabase import supabase

logger = logging.getLogger(__name__)

class GoogleIntegrationRepository:
    """Repository for Google integrations."""
    
    table_name = "google_integrations"
    
    @classmethod
    async def get_by_id(cls, integration_id: str) -> Optional[Dict[str, Any]]:
        """
        Get Google integration by ID.
        
        Args:
            integration_id: Integration ID
            
        Returns:
            Integration or None if not found
        """
        try:
            integrations = await supabase.select(
                cls.table_name,
                filters={"id": integration_id}
            )
            
            return integrations[0] if integrations else None
        except Exception as e:
            logger.error(f"Error getting Google integration by ID: {str(e)}")
            return None
    
    @classmethod
    async def get_by_user_id(cls, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Get Google integration by user ID.
        
        Args:
            user_id: User ID
            
        Returns:
            Integration or None if not found
        """
        try:
            integrations = await supabase.select(
                cls.table_name,
                filters={"user_id": user_id}
            )
            
            return integrations[0] if integrations else None
        except Exception as e:
            logger.error(f"Error getting Google integration by user ID: {str(e)}")
            return None
    
    @classmethod
    async def get_by_email(cls, email: str) -> Optional[Dict[str, Any]]:
        """
        Get Google integration by email.
        
        Args:
            email: Email address
            
        Returns:
            Integration or None if not found
        """
        try:
            integrations = await supabase.select(
                cls.table_name,
                filters={"email": email}
            )
            
            return integrations[0] if integrations else None
        except Exception as e:
            logger.error(f"Error getting Google integration by email: {str(e)}")
            return None
    
    @classmethod
    async def create(cls, integration_data: Dict[str, Any]) -> Optional[str]:
        """
        Create a new Google integration.
        
        Args:
            integration_data: Integration data
            
        Returns:
            ID of created integration or None if failed
        """
        try:
            result = await supabase.insert(cls.table_name, integration_data)
            
            return result[0]["id"] if result else None
        except Exception as e:
            logger.error(f"Error creating Google integration: {str(e)}")
            return None
    
    @classmethod
    async def update(cls, integration_id: str, integration_data: Dict[str, Any]) -> bool:
        """
        Update a Google integration.
        
        Args:
            integration_id: Integration ID
            integration_data: Updated integration data
            
        Returns:
            True if successful, False otherwise
        """
        try:
            result = await supabase.update(cls.table_name, integration_id, integration_data)
            
            return bool(result)
        except Exception as e:
            logger.error(f"Error updating Google integration: {str(e)}")
            return False
    
    @classmethod
    async def delete(cls, integration_id: str) -> bool:
        """
        Delete a Google integration.
        
        Args:
            integration_id: Integration ID
            
        Returns:
            True if successful, False otherwise
        """
        try:
            result = await supabase.delete(cls.table_name, integration_id)
            
            return result
        except Exception as e:
            logger.error(f"Error deleting Google integration: {str(e)}")
            return False