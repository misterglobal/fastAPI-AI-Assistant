import os
import logging
from typing import Dict, Optional, List, Any
import uuid
import json
from datetime import datetime

from app.integrations.twilio_integration import TwilioIntegration
from app.integrations.openai_integration import OpenAIIntegration
from app.repositories.agent_config_repository import AgentConfigRepository
from app.repositories.call_log_repository import CallLogRepository
from app.repositories.organization_repository import OrganizationRepository

logger = logging.getLogger(__name__)

class CallService:
    """Service for handling phone calls with AI agents."""
    
    def __init__(self):
        """Initialize the call service."""
        self.twilio = TwilioIntegration()
        self.openai = OpenAIIntegration()
        
    async def handle_incoming_call(self, call_data: Dict[str, Any], agent_config: Dict[str, Any]) -> str:
        """
        Handle an incoming call by setting up the initial TwiML response.
        
        Args:
            call_data: Information about the incoming call
            agent_config: Configuration for the AI agent
            
        Returns:
            TwiML response as string
        """
        try:
            # Get agent configuration
            greeting = agent_config.get("greeting", "Hello, this is an AI assistant. How may I help you today?")
            
            # Create initial call log
            call_log_data = {
                "organization_id": agent_config.get("organization_id"),
                "agent_id": agent_config.get("id"),
                "call_sid": call_data.get("CallSid"),
                "from_number": call_data.get("From"),
                "to_number": call_data.get("To"),
                "status": "in-progress",
                "duration": 0
            }
            
            await CallLogRepository.create(call_log_data)
            
            # Generate TwiML for initial greeting
            return self.twilio.create_initial_twiml(greeting)
            
        except Exception as e:
            logger.error(f"Error handling incoming call: {str(e)}")
            # Return a simple TwiML if there's an error
            return self.twilio.create_twiml_response(
                "I'm sorry, there was an error processing your call. Please try again later.", 
                gather=False
            )
    
    async def process_speech(self, call_data: Dict[str, Any], transcript: str) -> str:
        """
        Process speech from the caller and generate a response.
        
        Args:
            call_data: Information about the call
            transcript: Transcribed speech from the caller
            
        Returns:
            TwiML response as string
        """
        try:
            call_sid = call_data.get("CallSid")
            
            # Get call log and associated agent
            call_log = await CallLogRepository.get_by_call_sid(call_sid)
            
            if not call_log:
                logger.error(f"Call log not found for SID: {call_sid}")
                return self.twilio.create_goodbye_twiml("I'm sorry, there was an error. Goodbye.")
            
            agent_id = call_log.get("agent_id")
            agent_config = await AgentConfigRepository.get_by_id(agent_id)
            
            if not agent_config:
                logger.error(f"Agent config not found for ID: {agent_id}")
                return self.twilio.create_goodbye_twiml("I'm sorry, there was an error. Goodbye.")
            
            # Update call log with transcript
            current_transcript = call_log.get("transcript", "")
            if current_transcript:
                updated_transcript = f"{current_transcript}\nCaller: {transcript}"
            else:
                updated_transcript = f"Caller: {transcript}"
                
            await CallLogRepository.update(call_log.get("id"), {"transcript": updated_transcript})
            
            # Check for end call trigger words
            if any(word in transcript.lower() for word in ["goodbye", "bye", "end call", "hang up"]):
                goodbye_message = agent_config.get("goodbye", "Thank you for calling. Goodbye!")
                
                # Update call log with AI response
                final_transcript = f"{updated_transcript}\nAI: {goodbye_message}"
                await CallLogRepository.update(call_log.get("id"), {
                    "transcript": final_transcript,
                    "status": "completed"
                })
                
                return self.twilio.create_goodbye_twiml(goodbye_message)
            
            # Generate AI response based on transcript and system prompt
            system_prompt = agent_config.get("system_prompt", "You are a helpful AI assistant answering a phone call.")
            
            messages = [{"role": "user", "content": transcript}]
            ai_response = await self.openai.generate_response(messages, system_prompt=system_prompt)
            
            # Update call log with AI response
            updated_transcript = f"{updated_transcript}\nAI: {ai_response}"
            await CallLogRepository.update(call_log.get("id"), {"transcript": updated_transcript})
            
            # Create TwiML response with AI's message
            return self.twilio.create_twiml_response(ai_response)
            
        except Exception as e:
            logger.error(f"Error processing speech: {str(e)}")
            return self.twilio.create_twiml_response(
                "I'm sorry, I'm having trouble understanding. Could you please repeat that?", 
                gather=True
            )
    
    async def handle_call_status_update(self, call_data: Dict[str, Any]) -> bool:
        """
        Handle status updates for a call.
        
        Args:
            call_data: Status update information from Twilio
            
        Returns:
            True if successful, False otherwise
        """
        try:
            call_sid = call_data.get("CallSid")
            status = call_data.get("CallStatus")
            duration = call_data.get("CallDuration", 0)
            
            # Get call log
            call_log = await CallLogRepository.get_by_call_sid(call_sid)
            
            if not call_log:
                logger.warning(f"Call log not found for status update. SID: {call_sid}")
                return False
            
            update_data = {"status": status}
            
            # Add duration for completed calls
            if status in ["completed", "failed", "busy", "no-answer"]:
                update_data["duration"] = int(duration) if duration else 0
            
            # Get recording URL if call is completed
            if status == "completed":
                recording_url = await self.twilio.get_call_recording(call_sid)
                if recording_url:
                    update_data["recording_url"] = recording_url
                
                # Generate call summary if we have a transcript
                if call_log.get("transcript"):
                    try:
                        analysis = await self.openai.analyze_conversation(call_log["transcript"])
                        if analysis and "summary" in analysis:
                            update_data["summary"] = analysis["summary"]
                    except Exception as summary_error:
                        logger.error(f"Error generating call summary: {str(summary_error)}")
                
            # Update call log
            await CallLogRepository.update(call_log.get("id"), update_data)
            
            return True
            
        except Exception as e:
            logger.error(f"Error handling call status update: {str(e)}")
            return False

    async def make_call(self, phone_number: str, agent_id: str) -> Dict[str, Any]:
        """
        Initiate an outbound call using an agent.
        
        Args:
            phone_number: Phone number to call
            agent_id: ID of the agent to use for the call
            
        Returns:
            Call details
        """
        try:
            # Get agent configuration
            agent_config = await AgentConfigRepository.get_by_id(agent_id)
            
            if not agent_config:
                raise ValueError(f"Agent not found with ID: {agent_id}")
            
            # Make the call via Twilio
            call_result = await self.twilio.make_call(
                to_number=phone_number,
                agent_id=agent_id
            )
            
            # Create call log entry
            call_log_data = {
                "organization_id": agent_config.get("organization_id"),
                "agent_id": agent_id,
                "call_sid": call_result.get("sid"),
                "from_number": self.twilio.phone_number,
                "to_number": phone_number,
                "status": call_result.get("status", "queued"),
                "duration": 0
            }
            
            await CallLogRepository.create(call_log_data)
            
            return call_result
            
        except Exception as e:
            logger.error(f"Error making outbound call: {str(e)}")
            raise