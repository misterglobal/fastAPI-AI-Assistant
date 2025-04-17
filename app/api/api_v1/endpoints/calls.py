from fastapi import APIRouter, Depends, HTTPException, Request, Body, Query
from fastapi.responses import Response, HTMLResponse
from typing import Dict, Optional, List, Any
import logging

from app.core.auth import get_current_user
from app.services.call_service import CallService
from app.repositories.agent_config_repository import AgentConfigRepository
from app.repositories.call_log_repository import CallLogRepository

router = APIRouter()
call_service = CallService()
logger = logging.getLogger(__name__)

@router.post("/webhook")
async def call_webhook(request: Request):
    """
    Handle incoming call webhook from Twilio.
    """
    try:
        # Parse form data from Twilio
        form_data = await request.form()
        call_data = dict(form_data)
        
        # Get phone number to identify agent
        to_number = call_data.get("To")
        if not to_number:
            logger.error("No To number in call webhook")
            raise HTTPException(status_code=400, detail="Missing To number")
            
        # Get agent configuration for this phone number
        agent_config = await AgentConfigRepository.get_by_phone_number(to_number)
        
        if not agent_config:
            logger.error(f"No agent found for phone number: {to_number}")
            raise HTTPException(status_code=404, detail="Agent not found")
            
        # Handle the incoming call
        twiml_response = await call_service.handle_incoming_call(call_data, agent_config)
        
        # Return TwiML response
        return Response(content=twiml_response, media_type="application/xml")
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error handling call webhook: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/transcribe")
async def transcribe_speech(request: Request):
    """
    Handle speech transcription and response generation.
    """
    try:
        # Parse form data from Twilio
        form_data = await request.form()
        call_data = dict(form_data)
        
        # Get the transcribed speech
        speech_result = call_data.get("SpeechResult")
        
        if not speech_result:
            logger.warning("No speech result in transcription webhook")
            # Return a prompt for the caller to speak
            twiml = '<Response><Say>I didn\'t hear anything. Please try again.</Say><Gather input="speech" action="/api/v1/calls/transcribe" timeout="5" speechTimeout="auto" enhanced="true"/></Response>'
            return Response(content=twiml, media_type="application/xml")
            
        # Process the speech and generate a response
        twiml_response = await call_service.process_speech(call_data, speech_result)
        
        # Return TwiML response
        return Response(content=twiml_response, media_type="application/xml")
    
    except Exception as e:
        logger.error(f"Error handling transcription: {str(e)}")
        # Return a generic error response
        twiml = '<Response><Say>I\'m sorry, I encountered an error. Please try again later.</Say><Hangup/></Response>'
        return Response(content=twiml, media_type="application/xml")

@router.post("/status")
async def call_status(request: Request):
    """
    Handle call status callbacks from Twilio.
    """
    try:
        # Parse form data from Twilio
        form_data = await request.form()
        call_data = dict(form_data)
        
        # Process the status update
        await call_service.handle_call_status_update(call_data)
        
        # Return empty response
        return {}
    
    except Exception as e:
        logger.error(f"Error handling call status: {str(e)}")
        return {}  # Always return success to Twilio

@router.post("/make")
async def make_call(
    call_data: Dict[str, Any] = Body(...),
    current_user: Dict = Depends(get_current_user)
):
    """
    Make an outbound call.
    """
    try:
        phone_number = call_data.get("phone_number")
        agent_id = call_data.get("agent_id")
        
        if not phone_number or not agent_id:
            raise HTTPException(status_code=400, detail="Missing phone_number or agent_id")
            
        # Verify that the user has access to this agent
        agent = await AgentConfigRepository.get_by_id(agent_id)
        
        if not agent:
            raise HTTPException(status_code=404, detail="Agent not found")
            
        # Make the call
        call_result = await call_service.make_call(phone_number, agent_id)
        
        return {"success": True, "call": call_result}
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error making call: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/logs")
async def get_call_logs(
    agent_id: Optional[str] = Query(None),
    organization_id: Optional[str] = Query(None),
    limit: int = Query(20),
    offset: int = Query(0),
    current_user: Dict = Depends(get_current_user)
):
    """
    Get call logs with optional filtering.
    """
    try:
        filters = {}
        
        if agent_id:
            filters["agent_id"] = agent_id
            
        if organization_id:
            filters["organization_id"] = organization_id
            
        call_logs = await CallLogRepository.get_all(filters, limit, offset)
        
        return {"logs": call_logs, "count": len(call_logs)}
    
    except Exception as e:
        logger.error(f"Error getting call logs: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get call logs")

@router.get("/logs/{call_id}")
async def get_call_log(
    call_id: str,
    current_user: Dict = Depends(get_current_user)
):
    """
    Get a specific call log by ID.
    """
    try:
        call_log = await CallLogRepository.get_by_id(call_id)
        
        if not call_log:
            raise HTTPException(status_code=404, detail="Call log not found")
            
        return call_log
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting call log: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get call log")