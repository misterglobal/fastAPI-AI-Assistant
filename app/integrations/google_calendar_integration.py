import os
import logging
from typing import Dict, Any, Optional, List
import datetime
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import json

logger = logging.getLogger(__name__)

class GoogleCalendarIntegration:
    """Google Calendar integration for calendar management."""
    
    def __init__(self):
        """Initialize the Google Calendar integration."""
        self.client_id = os.environ.get("GOOGLE_CLIENT_ID")
        self.client_secret = os.environ.get("GOOGLE_CLIENT_SECRET")
        self.redirect_uri = os.environ.get("GOOGLE_REDIRECT_URI", "http://localhost:8000/api/v1/calendar/oauth_callback")
        
        # Required OAuth scopes
        self.scopes = [
            "https://www.googleapis.com/auth/calendar.readonly",
            "https://www.googleapis.com/auth/calendar.events"
        ]
        
        if not all([self.client_id, self.client_secret]):
            logger.warning("Google OAuth credentials not set. Calendar features will not work.")
    
    def get_authorization_url(self, state: str = None) -> str:
        """
        Get the Google OAuth authorization URL.
        
        Args:
            state: Optional state parameter for OAuth flow
            
        Returns:
            Authorization URL
        """
        if not all([self.client_id, self.client_secret]):
            raise ValueError("Google OAuth credentials not set")
            
        flow = Flow.from_client_config(
            {
                "web": {
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                    "redirect_uris": [self.redirect_uri]
                }
            },
            scopes=self.scopes,
            redirect_uri=self.redirect_uri
        )
        
        kwargs = {"access_type": "offline", "include_granted_scopes": "true"}
        if state:
            kwargs["state"] = state
            
        authorization_url, _ = flow.authorization_url(**kwargs)
        return authorization_url
    
    async def get_tokens_from_code(self, code: str) -> Dict[str, Any]:
        """
        Exchange authorization code for tokens.
        
        Args:
            code: Authorization code from OAuth callback
            
        Returns:
            Dictionary with access and refresh tokens
        """
        if not all([self.client_id, self.client_secret]):
            raise ValueError("Google OAuth credentials not set")
            
        flow = Flow.from_client_config(
            {
                "web": {
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                    "redirect_uris": [self.redirect_uri]
                }
            },
            scopes=self.scopes,
            redirect_uri=self.redirect_uri
        )
        
        flow.fetch_token(code=code)
        
        credentials = flow.credentials
        return {
            "access_token": credentials.token,
            "refresh_token": credentials.refresh_token,
            "token_uri": credentials.token_uri,
            "client_id": credentials.client_id,
            "client_secret": credentials.client_secret,
            "scopes": credentials.scopes,
            "expiry": credentials.expiry.isoformat() if credentials.expiry else None
        }
    
    def _get_credentials(self, token_info: Dict[str, Any]) -> Credentials:
        """
        Create Google credentials from token info.
        
        Args:
            token_info: Token information
            
        Returns:
            Google Credentials object
        """
        return Credentials(
            token=token_info["access_token"],
            refresh_token=token_info["refresh_token"],
            token_uri="https://oauth2.googleapis.com/token",
            client_id=self.client_id,
            client_secret=self.client_secret,
            scopes=token_info["scopes"]
        )
    
    async def list_calendars(self, token_info: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        List available calendars for a user.
        
        Args:
            token_info: User's token information
            
        Returns:
            List of calendar information
        """
        try:
            credentials = self._get_credentials(token_info)
            service = build("calendar", "v3", credentials=credentials)
            
            calendar_list = service.calendarList().list().execute()
            
            calendars = []
            for calendar_entry in calendar_list.get("items", []):
                calendars.append({
                    "id": calendar_entry["id"],
                    "summary": calendar_entry["summary"],
                    "description": calendar_entry.get("description", ""),
                    "timezone": calendar_entry.get("timeZone", "")
                })
                
            return calendars
        except Exception as e:
            logger.error(f"Error listing calendars: {str(e)}")
            raise
    
    async def get_free_busy(
        self,
        token_info: Dict[str, Any],
        calendar_ids: List[str],
        start_time: datetime.datetime,
        end_time: datetime.datetime
    ) -> Dict[str, List[Dict[str, str]]]:
        """
        Get free/busy information for calendars.
        
        Args:
            token_info: User's token information
            calendar_ids: List of calendar IDs to check
            start_time: Start time for the query
            end_time: End time for the query
            
        Returns:
            Dictionary mapping calendar IDs to busy time ranges
        """
        try:
            credentials = self._get_credentials(token_info)
            service = build("calendar", "v3", credentials=credentials)
            
            body = {
                "timeMin": start_time.isoformat(),
                "timeMax": end_time.isoformat(),
                "items": [{"id": cal_id} for cal_id in calendar_ids],
            }
            
            free_busy_request = service.freebusy().query(body=body).execute()
            
            result = {}
            for calendar_id, busy_data in free_busy_request.get("calendars", {}).items():
                result[calendar_id] = busy_data.get("busy", [])
                
            return result
        except Exception as e:
            logger.error(f"Error getting free/busy info: {str(e)}")
            raise
    
    async def find_available_slots(
        self,
        token_info: Dict[str, Any],
        calendar_id: str,
        start_date: datetime.date,
        end_date: datetime.date,
        day_start_time: datetime.time,
        day_end_time: datetime.time,
        duration_minutes: int = 30
    ) -> List[Dict[str, datetime.datetime]]:
        """
        Find available time slots in a calendar.
        
        Args:
            token_info: User's token information
            calendar_id: Calendar ID to check
            start_date: First date to check
            end_date: Last date to check
            day_start_time: Earliest time of day to consider
            day_end_time: Latest time of day to consider
            duration_minutes: Slot duration in minutes
            
        Returns:
            List of available time slots with start and end times
        """
        try:
            # Create datetime objects for the full range
            tz_info = datetime.timezone.utc  # Default to UTC
            range_start = datetime.datetime.combine(start_date, day_start_time, tz_info)
            range_end = datetime.datetime.combine(end_date, day_end_time, tz_info)
            
            # Get busy periods
            busy_periods = await self.get_free_busy(
                token_info,
                [calendar_id],
                range_start,
                range_end
            )
            
            # Extract busy times for this calendar
            calendar_busy = busy_periods.get(calendar_id, [])
            
            # Find available slots
            available_slots = []
            current_date = start_date
            
            while current_date <= end_date:
                day_start = datetime.datetime.combine(current_date, day_start_time, tz_info)
                day_end = datetime.datetime.combine(current_date, day_end_time, tz_info)
                
                # Skip this day if it's in the past
                if day_end < datetime.datetime.now(tz_info):
                    current_date += datetime.timedelta(days=1)
                    continue
                
                # Generate potential slots
                slot_start = day_start
                slot_duration = datetime.timedelta(minutes=duration_minutes)
                
                while slot_start + slot_duration <= day_end:
                    slot_end = slot_start + slot_duration
                    
                    # Check if slot overlaps with any busy periods
                    is_available = True
                    for busy in calendar_busy:
                        busy_start = datetime.datetime.fromisoformat(busy["start"])
                        busy_end = datetime.datetime.fromisoformat(busy["end"])
                        
                        # Check for overlap
                        if (slot_start < busy_end) and (slot_end > busy_start):
                            is_available = False
                            break
                    
                    # Add available slot
                    if is_available:
                        available_slots.append({
                            "start": slot_start,
                            "end": slot_end
                        })
                    
                    # Move to next potential slot
                    slot_start += datetime.timedelta(minutes=duration_minutes)
                
                # Move to next day
                current_date += datetime.timedelta(days=1)
            
            return available_slots
        except Exception as e:
            logger.error(f"Error finding available slots: {str(e)}")
            raise
    
    async def create_event(
        self,
        token_info: Dict[str, Any],
        calendar_id: str,
        summary: str,
        start_time: datetime.datetime,
        end_time: datetime.datetime,
        description: str = "",
        location: str = "",
        attendees: List[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Create a calendar event.
        
        Args:
            token_info: User's token information
            calendar_id: Calendar ID
            summary: Event title
            start_time: Event start time
            end_time: Event end time
            description: Event description
            location: Event location
            attendees: List of attendees with email and optional name
            
        Returns:
            Created event information
        """
        try:
            credentials = self._get_credentials(token_info)
            service = build("calendar", "v3", credentials=credentials)
            
            event = {
                "summary": summary,
                "description": description,
                "start": {
                    "dateTime": start_time.isoformat()
                },
                "end": {
                    "dateTime": end_time.isoformat()
                }
            }
            
            if location:
                event["location"] = location
                
            if attendees:
                event["attendees"] = attendees
                
            created_event = service.events().insert(
                calendarId=calendar_id,
                body=event,
                sendUpdates="all"
            ).execute()
            
            return {
                "id": created_event["id"],
                "summary": created_event["summary"],
                "htmlLink": created_event["htmlLink"],
                "start": created_event["start"],
                "end": created_event["end"]
            }
        except Exception as e:
            logger.error(f"Error creating event: {str(e)}")
            raise