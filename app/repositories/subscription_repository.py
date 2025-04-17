import logging
import uuid
from typing import Dict, List, Optional, Any

from app.core.supabase import supabase

logger = logging.getLogger(__name__)

class SubscriptionRepository:
    """Repository for user subscriptions."""
    
    table_name = "subscriptions"
    
    @classmethod
    async def get_by_id(cls, subscription_id: str) -> Optional[Dict[str, Any]]:
        """
        Get subscription by ID.
        
        Args:
            subscription_id: Subscription ID
            
        Returns:
            Subscription or None if not found
        """
        try:
            subscriptions = await supabase.select(
                cls.table_name,
                filters={"id": subscription_id}
            )
            
            return subscriptions[0] if subscriptions else None
        except Exception as e:
            logger.error(f"Error getting subscription by ID: {str(e)}")
            return None
    
    @classmethod
    async def get_by_organization(cls, organization_id: str) -> Optional[Dict[str, Any]]:
        """
        Get subscription by organization ID.
        
        Args:
            organization_id: Organization ID
            
        Returns:
            Subscription or None if not found
        """
        try:
            subscriptions = await supabase.select(
                cls.table_name,
                filters={"organization_id": organization_id}
            )
            
            return subscriptions[0] if subscriptions else None
        except Exception as e:
            logger.error(f"Error getting subscription by organization: {str(e)}")
            return None
    
    @classmethod
    async def get_by_user(cls, user_id: str) -> List[Dict[str, Any]]:
        """
        Get subscriptions for a user.
        
        Args:
            user_id: User ID
            
        Returns:
            List of subscriptions
        """
        try:
            return await supabase.select(
                cls.table_name,
                filters={"user_id": user_id}
            )
        except Exception as e:
            logger.error(f"Error getting subscriptions by user: {str(e)}")
            return []
    
    @classmethod
    async def create(cls, subscription_data: Dict[str, Any]) -> Optional[str]:
        """
        Create a new subscription.
        
        Args:
            subscription_data: Subscription data
            
        Returns:
            ID of created subscription or None if failed
        """
        try:
            # Ensure user_email field is present for RLS
            if "user_email" not in subscription_data:
                raise ValueError("user_email is required for creating subscriptions")
                
            result = await supabase.insert(cls.table_name, subscription_data)
            
            return result[0]["id"] if result else None
        except Exception as e:
            logger.error(f"Error creating subscription: {str(e)}")
            return None
    
    @classmethod
    async def update(cls, subscription_id: str, subscription_data: Dict[str, Any]) -> bool:
        """
        Update a subscription.
        
        Args:
            subscription_id: Subscription ID
            subscription_data: Updated subscription data
            
        Returns:
            True if successful, False otherwise
        """
        try:
            result = await supabase.update(cls.table_name, subscription_id, subscription_data)
            
            return bool(result)
        except Exception as e:
            logger.error(f"Error updating subscription: {str(e)}")
            return False
    
    @classmethod
    async def check_organization_limit(cls, organization_id: str, limit_name: str) -> Optional[Dict[str, Any]]:
        """
        Check subscription limits for an organization.
        
        Args:
            organization_id: Organization ID
            limit_name: Name of the limit to check (e.g., "agent_count", "call_minutes")
            
        Returns:
            Dictionary with limit information or None if no subscription
        """
        try:
            # Get current subscription
            subscription = await cls.get_by_organization(organization_id)
            
            if not subscription:
                return None
                
            # Get plan details
            plan_id = subscription.get("plan_id")
            status = subscription.get("status")
            
            # Check if subscription is active
            if status != "active":
                return {
                    "limit_name": limit_name,
                    "is_allowed": False,
                    "reason": "Subscription is not active",
                    "current": 0,
                    "max": 0
                }
                
            # Define limits based on plan
            # This would typically come from a plans table or configuration
            plan_limits = {
                "free": {
                    "agent_count": 1,
                    "call_minutes": 100,
                    "concurrent_calls": 3
                },
                "starter": {
                    "agent_count": 3,
                    "call_minutes": 500,
                    "concurrent_calls": 10
                },
                "pro": {
                    "agent_count": 10,
                    "call_minutes": 2000,
                    "concurrent_calls": 30
                },
                "enterprise": {
                    "agent_count": 50,
                    "call_minutes": 10000,
                    "concurrent_calls": 100
                }
            }
            
            # Get limits for the current plan
            plan_data = plan_limits.get(plan_id, plan_limits["free"])
            max_value = plan_data.get(limit_name, 0)
            
            # For usage-based limits, we would need to calculate current usage
            # This is a simplified example
            current_value = 0
            
            if limit_name == "agent_count":
                # Count agents for the organization
                # This would be implemented with a proper query
                current_value = 0  # Replace with actual count
                
            elif limit_name == "call_minutes":
                # Sum call minutes for the billing period
                # This would be implemented with a proper query
                current_value = 0  # Replace with actual usage
                
            elif limit_name == "concurrent_calls":
                # Get current concurrent calls
                # This would be tracked in a separate active calls table
                current_value = 0  # Replace with actual count
            
            return {
                "limit_name": limit_name,
                "is_allowed": current_value < max_value,
                "current": current_value,
                "max": max_value,
                "remaining": max(0, max_value - current_value)
            }
            
        except Exception as e:
            logger.error(f"Error checking organization limit: {str(e)}")
            # Default to allowing the operation if there's an error checking limits
            return {
                "limit_name": limit_name,
                "is_allowed": True,
                "reason": "Error checking limits",
                "current": 0,
                "max": 0
            }