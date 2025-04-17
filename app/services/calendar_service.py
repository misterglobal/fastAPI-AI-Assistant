import os
import logging
from typing import Dict, Optional, List, Any
import datetime
from dateutil.parser import parse

from app.integrations.google_calendar_integration import GoogleCalendarIntegration

logger = logging.getLogger(__name__)

class CalendarService:
    """Service for calendar management and scheduling."""
    
    def __init__(self):
        """Initialize the calendar service."""
        self.google_calendar = GoogleCalendarIntegration()
        
    def get_auth_url(self, user_id: str) -> str:
        """
        Get Google OAuth authorization URL.
        
        Args:
            user_id: User ID for state parameter
            
        Returns:
            Authorization URL
        """
        try:
            state = user_id  # Use user ID as state for callback identification
            return self.google_calendar.get_authorization_url(state)
            
        except Exception as e:
            logger.error(f"Error getting auth URL: {str(e)}")
            raise
    
    async def process_auth_callback(self, code: str) -> Dict[str, Any]:
        """
        Process OAuth callback and get tokens.
        
        Args:
            code: Authorization code from callback
            
        Returns:
            Token information
        """
        try:
            return await self.google_calendar.get_tokens_from_code(code)
            
        except Exception as e:
            logger.error(f"Error processing auth callback: {str(e)}")
            raise
    
    async def get_calendars(self, token_info: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Get user's calendars.
        
        Args:
            token_info: User's token information
            
        Returns:
            List of calendars
        """
        try:
            return await self.google_calendar.list_calendars(token_info)
            
        except Exception as e:
            logger.error(f"Error getting calendars: {str(e)}")
            raise
    
    async def get_available_slots(
        self,
        token_info: Dict[str, Any],
        calendar_id: str,
        date_range: Dict[str, str],
        business_hours: Dict[str, Any],
        duration_minutes: int = 30
    ) -> List[Dict[str, Any]]:
        """
        Get available time slots for scheduling.
        
        Args:
            token_info: User's token information
            calendar_id: Calendar ID to check
            date_range: Start and end dates
            business_hours: Business hours configuration
            duration_minutes: Duration of slots in minutes
            
        Returns:
            List of available time slots
        """
        try:
            # Parse date range
            start_date = parse(date_range["start"]).date()
            end_date = parse(date_range["end"]).date()
            
            # Parse business hours
            day_start_time = datetime.time(
                hour=int(business_hours.get("start_hour", 9)),
                minute=int(business_hours.get("start_minute", 0))
            )
            
            day_end_time = datetime.time(
                hour=int(business_hours.get("end_hour", 17)),
                minute=int(business_hours.get("end_minute", 0))
            )
            
            return await self.google_calendar.find_available_slots(
                token_info=token_info,
                calendar_id=calendar_id,
                start_date=start_date,
                end_date=end_date,
                day_start_time=day_start_time,
                day_end_time=day_end_time,
                duration_minutes=duration_minutes
            )
            
        except Exception as e:
            logger.error(f"Error getting available slots: {str(e)}")
            raise
    
    async def schedule_appointment(
        self,
        token_info: Dict[str, Any],
        calendar_id: str,
        appointment_info: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Schedule an appointment.
        
        Args:
            token_info: User's token information
            calendar_id: Calendar ID
            appointment_info: Appointment details
            
        Returns:
            Created event information
        """
        try:
            # Parse start and end times
            start_time = parse(appointment_info["start_time"])
            end_time = parse(appointment_info["end_time"])
            
            # Create the event
            return await self.google_calendar.create_event(
                token_info=token_info,
                calendar_id=calendar_id,
                summary=appointment_info["summary"],
                start_time=start_time,
                end_time=end_time,
                description=appointment_info.get("description", ""),
                location=appointment_info.get("location", ""),
                attendees=appointment_info.get("attendees", [])
            )
            
        except Exception as e:
            logger.error(f"Error scheduling appointment: {str(e)}")
            raise
    
    async def check_availability(
        self,
        token_info: Dict[str, Any],
        calendar_id: str,
        start_time: str,
        end_time: str
    ) -> bool:
        """
        Check if a time slot is available.
        
        Args:
            token_info: User's token information
            calendar_id: Calendar ID
            start_time: Start time as ISO string
            end_time: End time as ISO string
            
        Returns:
            True if available, False if busy
        """
        try:
            # Parse times
            start = parse(start_time)
            end = parse(end_time)
            
            # Get busy periods
            busy_periods = await self.google_calendar.get_free_busy(
                token_info=token_info,
                calendar_ids=[calendar_id],
                start_time=start,
                end_time=end
            )
            
            # Check if there are any busy periods for this calendar
            return len(busy_periods.get(calendar_id, [])) == 0
            
        except Exception as e:
            logger.error(f"Error checking availability: {str(e)}")
            raise