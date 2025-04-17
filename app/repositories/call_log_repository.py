import logging
import uuid
from typing import Dict, List, Optional, Any

from app.core.supabase import supabase

logger = logging.getLogger(__name__)

class CallLogRepository:
    """Repository for call logs."""
    
    table_name = "call_logs"
    
    @classmethod
    async def get_by_id(cls, call_id: str) -> Optional[Dict[str, Any]]:
        """
        Get call log by ID.
        
        Args:
            call_id: Call log ID
            
        Returns:
            Call log or None if not found
        """
        try:
            call_logs = await supabase.select(
                cls.table_name,
                filters={"id": call_id}
            )
            
            return call_logs[0] if call_logs else None
        except Exception as e:
            logger.error(f"Error getting call log by ID: {str(e)}")
            return None
    
    @classmethod
    async def get_by_call_sid(cls, call_sid: str) -> Optional[Dict[str, Any]]:
        """
        Get call log by Twilio call SID.
        
        Args:
            call_sid: Twilio call SID
            
        Returns:
            Call log or None if not found
        """
        try:
            call_logs = await supabase.select(
                cls.table_name,
                filters={"call_sid": call_sid}
            )
            
            return call_logs[0] if call_logs else None
        except Exception as e:
            logger.error(f"Error getting call log by SID: {str(e)}")
            return None
    
    @classmethod
    async def get_all(
        cls, 
        filters: Optional[Dict[str, Any]] = None, 
        limit: int = 100, 
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        Get all call logs with optional filtering.
        
        Args:
            filters: Optional filters
            limit: Maximum number of records to return
            offset: Offset for pagination
            
        Returns:
            List of call logs
        """
        try:
            # TODO: Implement pagination with limit and offset
            return await supabase.select(
                cls.table_name,
                filters=filters or {}
            )
        except Exception as e:
            logger.error(f"Error getting call logs: {str(e)}")
            return []
    
    @classmethod
    async def get_all_by_organization(
        cls, 
        organization_id: str,
        limit: int = 100, 
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        Get all call logs for an organization.
        
        Args:
            organization_id: Organization ID
            limit: Maximum number of records to return
            offset: Offset for pagination
            
        Returns:
            List of call logs
        """
        try:
            return await supabase.select(
                cls.table_name,
                filters={"organization_id": organization_id}
            )
        except Exception as e:
            logger.error(f"Error getting call logs by organization: {str(e)}")
            return []
    
    @classmethod
    async def create(cls, call_log_data: Dict[str, Any]) -> Optional[str]:
        """
        Create a new call log.
        
        Args:
            call_log_data: Call log data
            
        Returns:
            ID of created call log or None if failed
        """
        try:
            result = await supabase.insert(cls.table_name, call_log_data)
            
            return result[0]["id"] if result else None
        except Exception as e:
            logger.error(f"Error creating call log: {str(e)}")
            return None
    
    @classmethod
    async def update(cls, call_id: str, call_log_data: Dict[str, Any]) -> bool:
        """
        Update a call log.
        
        Args:
            call_id: Call log ID
            call_log_data: Updated call log data
            
        Returns:
            True if successful, False otherwise
        """
        try:
            result = await supabase.update(cls.table_name, call_id, call_log_data)
            
            return bool(result)
        except Exception as e:
            logger.error(f"Error updating call log: {str(e)}")
            return False
    
    @classmethod
    async def delete(cls, call_id: str) -> bool:
        """
        Delete a call log.
        
        Args:
            call_id: Call log ID
            
        Returns:
            True if successful, False otherwise
        """
        try:
            result = await supabase.delete(cls.table_name, call_id)
            
            return result
        except Exception as e:
            logger.error(f"Error deleting call log: {str(e)}")
            return False