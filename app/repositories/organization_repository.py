import logging
import uuid
from typing import Dict, List, Optional, Any

from app.core.supabase import supabase

logger = logging.getLogger(__name__)

class OrganizationRepository:
    """Repository for organizations."""
    
    table_name = "organizations"
    
    @classmethod
    async def get_by_id(cls, org_id: str) -> Optional[Dict[str, Any]]:
        """
        Get organization by ID.
        
        Args:
            org_id: Organization ID
            
        Returns:
            Organization or None if not found
        """
        try:
            orgs = await supabase.select(
                cls.table_name,
                filters={"id": org_id}
            )
            
            return orgs[0] if orgs else None
        except Exception as e:
            logger.error(f"Error getting organization by ID: {str(e)}")
            return None
    
    @classmethod
    async def get_by_owner(cls, owner_id: str) -> List[Dict[str, Any]]:
        """
        Get organizations by owner ID.
        
        Args:
            owner_id: Owner ID
            
        Returns:
            List of organizations
        """
        try:
            return await supabase.select(
                cls.table_name,
                filters={"owner_id": owner_id}
            )
        except Exception as e:
            logger.error(f"Error getting organizations by owner: {str(e)}")
            return []
    
    @classmethod
    async def create(cls, org_data) -> Optional[str]:
        """
        Create a new organization.
        
        Args:
            org_data: Organization data
            
        Returns:
            ID of created organization or None if failed
        """
        try:
            # Generate UUID if not provided
            if not org_data.get("id"):
                # Convert Pydantic model to dict if needed
                if hasattr(org_data, "dict"):
                    org_data = org_data.dict()
            
            result = await supabase.insert(cls.table_name, org_data)
            
            return result[0]["id"] if result else None
        except Exception as e:
            logger.error(f"Error creating organization: {str(e)}")
            return None
    
    @classmethod
    async def update(cls, org_id: str, org_data) -> bool:
        """
        Update an organization.
        
        Args:
            org_id: Organization ID
            org_data: Updated organization data
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Convert Pydantic model to dict if needed
            if hasattr(org_data, "dict"):
                org_data = org_data.dict(exclude_unset=True)
                
            result = await supabase.update(cls.table_name, org_id, org_data)
            
            return bool(result)
        except Exception as e:
            logger.error(f"Error updating organization: {str(e)}")
            return False
    
    @classmethod
    async def delete(cls, org_id: str) -> bool:
        """
        Delete an organization.
        
        Args:
            org_id: Organization ID
            
        Returns:
            True if successful, False otherwise
        """
        try:
            result = await supabase.delete(cls.table_name, org_id)
            
            return result
        except Exception as e:
            logger.error(f"Error deleting organization: {str(e)}")
            return False