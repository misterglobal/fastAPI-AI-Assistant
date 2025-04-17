import logging
import uuid
from typing import Dict, List, Optional, Any

from app.core.supabase import supabase

logger = logging.getLogger(__name__)

class AgentConfigRepository:
    """Repository for agent configurations."""
    
    table_name = "agent_configs"
    
    @classmethod
    async def get_by_id(cls, agent_id: str) -> Optional[Dict[str, Any]]:
        """
        Get agent configuration by ID.
        
        Args:
            agent_id: Agent ID
            
        Returns:
            Agent configuration or None if not found
        """
        try:
            agents = await supabase.select(
                cls.table_name,
                filters={"id": agent_id}
            )
            
            return agents[0] if agents else None
        except Exception as e:
            logger.error(f"Error getting agent by ID: {str(e)}")
            return None
    
    @classmethod
    async def get_by_phone_number(cls, phone_number: str) -> Optional[Dict[str, Any]]:
        """
        Get agent configuration by phone number.
        
        Args:
            phone_number: Phone number
            
        Returns:
            Agent configuration or None if not found
        """
        try:
            agents = await supabase.select(
                cls.table_name,
                filters={"phone_number": phone_number}
            )
            
            return agents[0] if agents else None
        except Exception as e:
            logger.error(f"Error getting agent by phone number: {str(e)}")
            return None
    
    @classmethod
    async def get_all_by_organization(cls, organization_id: str) -> List[Dict[str, Any]]:
        """
        Get all agent configurations for an organization.
        
        Args:
            organization_id: Organization ID
            
        Returns:
            List of agent configurations
        """
        try:
            return await supabase.select(
                cls.table_name,
                filters={"organization_id": organization_id}
            )
        except Exception as e:
            logger.error(f"Error getting agents by organization: {str(e)}")
            return []
    
    @classmethod
    async def create(cls, agent_data) -> Optional[str]:
        """
        Create a new agent configuration.
        
        Args:
            agent_data: Agent configuration data
            
        Returns:
            ID of created agent or None if failed
        """
        try:
            # Generate UUID if not provided
            if not agent_data.get("id"):
                agent_data.dict = lambda: {**agent_data}
                agent_data = agent_data.dict()
            
            result = await supabase.insert(cls.table_name, agent_data)
            
            return result[0]["id"] if result else None
        except Exception as e:
            logger.error(f"Error creating agent: {str(e)}")
            return None
    
    @classmethod
    async def update(cls, agent_id: str, agent_data) -> bool:
        """
        Update an agent configuration.
        
        Args:
            agent_id: Agent ID
            agent_data: Updated agent data
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Convert Pydantic model to dict if needed
            if hasattr(agent_data, "dict"):
                agent_data = agent_data.dict(exclude_unset=True)
                
            result = await supabase.update(cls.table_name, agent_id, agent_data)
            
            return bool(result)
        except Exception as e:
            logger.error(f"Error updating agent: {str(e)}")
            return False
    
    @classmethod
    async def delete(cls, agent_id: str) -> bool:
        """
        Delete an agent configuration.
        
        Args:
            agent_id: Agent ID
            
        Returns:
            True if successful, False otherwise
        """
        try:
            result = await supabase.delete(cls.table_name, agent_id)
            
            return result
        except Exception as e:
            logger.error(f"Error deleting agent: {str(e)}")
            return False