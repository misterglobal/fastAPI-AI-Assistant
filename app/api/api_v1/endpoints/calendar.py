from fastapi import APIRouter, Depends, HTTPException, Request, Body, Query
from fastapi.responses import RedirectResponse
from typing import Dict, Optional, List, Any
import logging
import os

from app.core.auth import get_current_user
from app.services.calendar_service import CalendarService
from app.repositories.google_integration_repository import GoogleIntegrationRepository

router = APIRouter()
calendar_service = CalendarService()
logger = logging.getLogger(__name__)

@router.post("/connect")
async def connect_google_calendar(
    current_user: Dict = Depends(get_current_user)
):
    """
    Start OAuth flow to connect Google Calendar.
    """
    try:
        user_id = current_user.get("sub")
        
        # Generate authorization URL
        auth_url = calendar_service.get_auth_url(user_id)
        
        return {"auth_url": auth_url}
    
    except Exception as e:
        logger.error(f"Error starting OAuth flow: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to start OAuth flow")

@router.get("/oauth_callback")
async def oauth_callback(code: str, state: Optional[str] = None):
    """
    Handle OAuth callback from Google.
    """
    try:
        # Process the authorization code
        token_info = await calendar_service.process_auth_callback(code)
        
        # Store token information
        if state:
            user_id = state  # We stored user ID as state
            
            # Get user email from token_info when we have it
            # For now, just use a placeholder
            user_email = ""  # This would come from Google API
            
            integration_data = {
                "user_id": user_id,
                "email": user_email,
                "access_token": token_info["access_token"],
                "refresh_token": token_info["refresh_token"],
                "scopes": ",".join(token_info["scopes"])
            }
            
            await GoogleIntegrationRepository.create(integration_data)
        
        # Redirect to frontend with success parameter
        frontend_url = os.environ.get("FRONTEND_URL", "http://localhost:3000")
        return RedirectResponse(url=f"{frontend_url}/calendar?success=true")
    
    except Exception as e:
        logger.error(f"Error processing OAuth callback: {str(e)}")
        # Redirect to frontend with error parameter
        frontend_url = os.environ.get("FRONTEND_URL", "http://localhost:3000")
        return RedirectResponse(url=f"{frontend_url}/calendar?error=true")

@router.get("/calendars")
async def list_calendars(current_user: Dict = Depends(get_current_user)):
    """
    List user's Google Calendars.
    """
    try:
        user_id = current_user.get("sub")
        
        # Get user's Google integration
        integration = await GoogleIntegrationRepository.get_by_user_id(user_id)
        
        if not integration:
            raise HTTPException(status_code=404, detail="Google Calendar not connected")
            
        # Construct token info
        token_info = {
            "access_token": integration["access_token"],
            "refresh_token": integration["refresh_token"],
            "scopes": integration["scopes"].split(",")
        }
        
        # Get calendars
        calendars = await calendar_service.get_calendars(token_info)
        
        return {"calendars": calendars}
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing calendars: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to list calendars")

@router.post("/available-slots")
async def get_available_slots(
    data: Dict[str, Any] = Body(...),
    current_user: Dict = Depends(get_current_user)
):
    """
    Get available time slots for scheduling.
    """
    try:
        user_id = current_user.get("sub")
        
        calendar_id = data.get("calendar_id")
        date_range = data.get("date_range")
        business_hours = data.get("business_hours")
        duration_minutes = data.get("duration_minutes", 30)
        
        if not all([calendar_id, date_range, business_hours]):
            raise HTTPException(status_code=400, detail="Missing required parameters")
            
        # Get user's Google integration
        integration = await GoogleIntegrationRepository.get_by_user_id(user_id)
        
        if not integration:
            raise HTTPException(status_code=404, detail="Google Calendar not connected")
            
        # Construct token info
        token_info = {
            "access_token": integration["access_token"],
            "refresh_token": integration["refresh_token"],
            "scopes": integration["scopes"].split(",")
        }
        
        # Get available slots
        slots = await calendar_service.get_available_slots(
            token_info=token_info,
            calendar_id=calendar_id,
            date_range=date_range,
            business_hours=business_hours,
            duration_minutes=duration_minutes
        )
        
        # Format slots for frontend
        formatted_slots = []
        for slot in slots:
            formatted_slots.append({
                "start": slot["start"].isoformat(),
                "end": slot["end"].isoformat()
            })
        
        return {"slots": formatted_slots}
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting available slots: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get available slots")

@router.post("/schedule")
async def schedule_appointment(
    data: Dict[str, Any] = Body(...),
    current_user: Dict = Depends(get_current_user)
):
    """
    Schedule an appointment.
    """
    try:
        user_id = current_user.get("sub")
        
        calendar_id = data.get("calendar_id")
        appointment_info = data.get("appointment")
        
        if not all([calendar_id, appointment_info]):
            raise HTTPException(status_code=400, detail="Missing required parameters")
            
        # Get user's Google integration
        integration = await GoogleIntegrationRepository.get_by_user_id(user_id)
        
        if not integration:
            raise HTTPException(status_code=404, detail="Google Calendar not connected")
            
        # Construct token info
        token_info = {
            "access_token": integration["access_token"],
            "refresh_token": integration["refresh_token"],
            "scopes": integration["scopes"].split(",")
        }
        
        # Schedule appointment
        event = await calendar_service.schedule_appointment(
            token_info=token_info,
            calendar_id=calendar_id,
            appointment_info=appointment_info
        )
        
        return {"event": event}
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error scheduling appointment: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to schedule appointment")

@router.post("/update-integration")
async def update_integration(
    data: Dict[str, Any] = Body(...),
    current_user: Dict = Depends(get_current_user)
):
    """
    Update Google Calendar integration settings.
    """
    try:
        user_id = current_user.get("sub")
        
        calendar_id = data.get("calendar_id")
        availability_days = data.get("availability_days")
        availability_start = data.get("availability_start")
        availability_end = data.get("availability_end")
        
        # Get user's Google integration
        integration = await GoogleIntegrationRepository.get_by_user_id(user_id)
        
        if not integration:
            raise HTTPException(status_code=404, detail="Google Calendar not connected")
            
        # Update integration settings
        update_data = {}
        
        if calendar_id:
            update_data["calendar_id"] = calendar_id
            
        if availability_days:
            update_data["availability_days"] = availability_days
            
        if availability_start:
            update_data["availability_start"] = availability_start
            
        if availability_end:
            update_data["availability_end"] = availability_end
            
        if update_data:
            await GoogleIntegrationRepository.update(integration["id"], update_data)
        
        return {"message": "Integration settings updated"}
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating integration: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to update integration settings")