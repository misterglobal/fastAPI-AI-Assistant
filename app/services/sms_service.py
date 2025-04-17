import os
import logging
from typing import Dict, Optional, List, Any
import uuid
import json

from app.integrations.twilio_integration import TwilioIntegration
from app.integrations.openai_integration import OpenAIIntegration
from app.repositories.agent_config_repository import AgentConfigRepository
from app.repositories.organization_repository import OrganizationRepository

logger = logging.getLogger(__name__)

class SMSService:
    """Service for handling SMS messages with AI agents."""
    
    def __init__(self):
        """Initialize the SMS service."""
        self.twilio = TwilioIntegration()
        self.openai = OpenAIIntegration()
    
    async def handle_incoming_sms(self, sms_data: Dict[str, Any]) -> str:
        """
        Handle an incoming SMS message.
        
        Args:
            sms_data: Information about the incoming SMS
            
        Returns:
            Response message
        """
        try:
            from_number = sms_data.get("From")
            to_number = sms_data.get("To")
            body = sms_data.get("Body", "").strip()
            
            if not all([from_number, to_number, body]):
                logger.error("Missing required SMS data")
                return "We're sorry, we couldn't process your message. Please try again later."
                
            # Find agent configuration for the receiving phone number
            agent_config = await AgentConfigRepository.get_by_phone_number(to_number)
            
            if not agent_config:
                logger.error(f"No agent configured for phone number: {to_number}")
                return "This number is not currently configured to respond to messages."
            
            # Generate response based on agent configuration
            system_prompt = agent_config.get("system_prompt", "You are a helpful AI assistant responding to SMS messages.")
            
            # Add SMS context to the prompt
            sms_system_prompt = f"{system_prompt}\n\nYou are communicating via SMS text message. Keep responses concise (under 160 characters when possible) and professional. You're representing the business. Don't use emojis unless the user does first."
            
            messages = [{"role": "user", "content": body}]
            ai_response = await self.openai.generate_response(messages, system_prompt=sms_system_prompt, max_tokens=300)
            
            return ai_response
            
        except Exception as e:
            logger.error(f"Error handling incoming SMS: {str(e)}")
            return "We're sorry, we're experiencing technical difficulties. Please try again later."
    
    async def send_sms(self, phone_number: str, message: str, agent_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Send an SMS message.
        
        Args:
            phone_number: Phone number to send to
            message: Message content
            agent_id: Optional agent ID to use for context
            
        Returns:
            SMS details
        """
        try:
            # If agent_id is provided, get agent configuration
            agent_config = None
            if agent_id:
                agent_config = await AgentConfigRepository.get_by_id(agent_id)
                
                # If agent has a specific phone number to use, use that
                if agent_config and agent_config.get("phone_number"):
                    return await self.twilio.send_sms(
                        to_number=phone_number,
                        message=message
                    )
            
            # Otherwise use default Twilio phone number
            return await self.twilio.send_sms(
                to_number=phone_number,
                message=message
            )
            
        except Exception as e:
            logger.error(f"Error sending SMS: {str(e)}")
            raise
    
    async def send_ai_response(self, phone_number: str, user_message: str, agent_id: str) -> Dict[str, Any]:
        """
        Generate an AI response to a message and send it as an SMS.
        
        Args:
            phone_number: Phone number to send to
            user_message: User's message to respond to
            agent_id: Agent ID to use for generating response
            
        Returns:
            SMS details
        """
        try:
            # Get agent configuration
            agent_config = await AgentConfigRepository.get_by_id(agent_id)
            
            if not agent_config:
                raise ValueError(f"Agent not found with ID: {agent_id}")
            
            # Generate AI response
            system_prompt = agent_config.get("system_prompt", "You are a helpful AI assistant responding to SMS messages.")
            
            # Add SMS context to the prompt
            sms_system_prompt = f"{system_prompt}\n\nYou are communicating via SMS text message. Keep responses concise (under 160 characters when possible) and professional. You're representing the business. Don't use emojis unless the user does first."
            
            messages = [{"role": "user", "content": user_message}]
            ai_response = await self.openai.generate_response(messages, system_prompt=sms_system_prompt, max_tokens=300)
            
            # Send the response
            return await self.send_sms(phone_number, ai_response, agent_id)
            
        except Exception as e:
            logger.error(f"Error sending AI response via SMS: {str(e)}")
            raise