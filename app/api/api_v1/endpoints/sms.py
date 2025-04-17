from fastapi import APIRouter, Depends, HTTPException, Request, Body, Query
from fastapi.responses import Response
from typing import Dict, Optional, Any
import logging

from app.core.auth import get_current_user
from app.services.sms_service import SMSService
from app.repositories.agent_config_repository import AgentConfigRepository

router = APIRouter()
sms_service = SMSService()
logger = logging.getLogger(__name__)

@router.post("/webhook")
async def sms_webhook(request: Request):
    """
    Handle incoming SMS webhook from Twilio.
    """
    try:
        # Parse form data from Twilio
        form_data = await request.form()
        sms_data = dict(form_data)
        
        # Get the response for the SMS
        response = await sms_service.handle_incoming_sms(sms_data)
        
        # Return TwiML response
        twiml = f'<Response><Message>{response}</Message></Response>'
        return Response(content=twiml, media_type="application/xml")
    
    except Exception as e:
        logger.error(f"Error handling SMS webhook: {str(e)}")
        # Return a generic error response
        twiml = '<Response><Message>Sorry, we couldn\'t process your message. Please try again later.</Message></Response>'
        return Response(content=twiml, media_type="application/xml")

@router.post("/send")
async def send_sms(
    sms_data: Dict[str, Any] = Body(...),
    current_user: Dict = Depends(get_current_user)
):
    """
    Send an SMS message.
    """
    try:
        phone_number = sms_data.get("phone_number")
        message = sms_data.get("message")
        agent_id = sms_data.get("agent_id")
        
        if not phone_number or not message:
            raise HTTPException(status_code=400, detail="Missing phone_number or message")
            
        # If agent ID provided, verify access
        if agent_id:
            agent = await AgentConfigRepository.get_by_id(agent_id)
            
            if not agent:
                raise HTTPException(status_code=404, detail="Agent not found")
                
        # Send the SMS
        sms_result = await sms_service.send_sms(phone_number, message, agent_id)
        
        return {"success": True, "sms": sms_result}
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error sending SMS: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/ai-response")
async def send_ai_response(
    data: Dict[str, Any] = Body(...),
    current_user: Dict = Depends(get_current_user)
):
    """
    Generate and send an AI response to a message via SMS.
    """
    try:
        phone_number = data.get("phone_number")
        user_message = data.get("message")
        agent_id = data.get("agent_id")
        
        if not all([phone_number, user_message, agent_id]):
            raise HTTPException(status_code=400, detail="Missing required parameters")
            
        # Verify that the user has access to this agent
        agent = await AgentConfigRepository.get_by_id(agent_id)
        
        if not agent:
            raise HTTPException(status_code=404, detail="Agent not found")
            
        # Generate AI response and send it
        sms_result = await sms_service.send_ai_response(phone_number, user_message, agent_id)
        
        return {"success": True, "sms": sms_result}
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error sending AI response: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))