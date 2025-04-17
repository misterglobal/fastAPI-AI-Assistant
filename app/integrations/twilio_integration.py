import os
import logging
import json
from typing import Dict, Any, Optional, List
from twilio.rest import Client
from twilio.twiml.voice_response import VoiceResponse, Gather
from urllib.parse import urljoin
import httpx

logger = logging.getLogger(__name__)

class TwilioIntegration:
    """Twilio integration for handling phone calls and SMS."""

    def __init__(self, base_url: str = None):
        """
        Initialize the Twilio integration.
        
        Args:
            base_url: Base URL for callbacks, defaults to environment variable
        """
        self.account_sid = os.environ.get("TWILIO_ACCOUNT_SID")
        self.auth_token = os.environ.get("TWILIO_AUTH_TOKEN")
        self.phone_number = os.environ.get("TWILIO_PHONE_NUMBER")
        self.base_url = base_url or os.environ.get("BASE_URL", "http://localhost:8000")
        
        if not all([self.account_sid, self.auth_token]):
            logger.warning("Twilio credentials not set. Some features will not work.")
            self.client = None
        else:
            self.client = Client(self.account_sid, self.auth_token)

    def generate_webhook_url(self, path: str) -> str:
        """
        Generate a full webhook URL.
        
        Args:
            path: Relative path for the webhook
            
        Returns:
            Full webhook URL
        """
        return urljoin(self.base_url, path)

    async def make_call(self, to_number: str, webhook_url: str = None, agent_id: str = None) -> Dict[str, Any]:
        """
        Make an outbound call.
        
        Args:
            to_number: Phone number to call
            webhook_url: Webhook URL for TwiML instructions
            agent_id: Optional agent ID to include in the webhook
            
        Returns:
            Call details
        """
        if not self.client:
            raise ValueError("Twilio client not initialized. Check credentials.")
            
        if not webhook_url:
            if not agent_id:
                raise ValueError("Either webhook_url or agent_id must be provided")
            webhook_url = self.generate_webhook_url(f"/api/v1/calls/handle?agent_id={agent_id}")
            
        try:
            call = self.client.calls.create(
                to=to_number,
                from_=self.phone_number,
                url=webhook_url,
                status_callback=self.generate_webhook_url("/api/v1/calls/status"),
                record=True
            )
            return {
                "sid": call.sid,
                "status": call.status,
                "direction": call.direction
            }
        except Exception as e:
            logger.error(f"Error making Twilio call: {str(e)}")
            raise
            
    async def send_sms(self, to_number: str, message: str) -> Dict[str, Any]:
        """
        Send an SMS message.
        
        Args:
            to_number: Phone number to send to
            message: Message content
            
        Returns:
            SMS details
        """
        if not self.client:
            raise ValueError("Twilio client not initialized. Check credentials.")
            
        try:
            message = self.client.messages.create(
                to=to_number,
                from_=self.phone_number,
                body=message
            )
            return {
                "sid": message.sid,
                "status": message.status,
                "direction": message.direction
            }
        except Exception as e:
            logger.error(f"Error sending SMS: {str(e)}")
            raise
            
    def create_initial_twiml(self, greeting: str = None) -> str:
        """
        Create initial TwiML for inbound calls.
        
        Args:
            greeting: Optional greeting message
            
        Returns:
            TwiML as string
        """
        response = VoiceResponse()
        
        if greeting:
            response.say(greeting)
        
        gather = Gather(
            input='speech',
            action='/api/v1/calls/transcribe',
            timeout=5,
            speechTimeout='auto',
            enhanced=True
        )
        
        return str(response)
        
    def create_twiml_response(self, text_to_say: str, gather: bool = True) -> str:
        """
        Create TwiML for responding during calls.
        
        Args:
            text_to_say: Text to say to caller
            gather: Whether to gather user input
            
        Returns:
            TwiML as string
        """
        response = VoiceResponse()
        
        # Add the text to say
        response.say(text_to_say)
        
        if gather:
            # Wait for user input
            gather = Gather(
                input='speech',
                action='/api/v1/calls/transcribe',
                timeout=2,
                speechTimeout='auto',
                enhanced=True
            )
            response.append(gather)
        
        return str(response)
    
    def create_goodbye_twiml(self, goodbye_message: str) -> str:
        """
        Create TwiML for ending calls.
        
        Args:
            goodbye_message: Goodbye message
            
        Returns:
            TwiML as string
        """
        response = VoiceResponse()
        response.say(goodbye_message)
        response.hangup()
        return str(response)
        
    async def get_call_recording(self, call_sid: str) -> Optional[str]:
        """
        Get recording URL for a completed call.
        
        Args:
            call_sid: Call SID
            
        Returns:
            Recording URL or None if not available
        """
        if not self.client:
            raise ValueError("Twilio client not initialized. Check credentials.")
            
        try:
            recordings = self.client.recordings.list(call_sid=call_sid)
            if recordings:
                # Get the most recent recording
                recording = recordings[0]
                return f"https://api.twilio.com/2010-04-01/Accounts/{self.account_sid}/Recordings/{recording.sid}.mp3"
            return None
        except Exception as e:
            logger.error(f"Error getting call recording: {str(e)}")
            return None