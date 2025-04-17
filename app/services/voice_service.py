import os
import logging
from typing import Dict, Optional, List, Any
import uuid
import tempfile
import base64

from app.integrations.elevenlabs_integration import ElevenLabsIntegration

logger = logging.getLogger(__name__)

class VoiceService:
    """Service for voice synthesis and processing."""
    
    def __init__(self):
        """Initialize the voice service."""
        self.elevenlabs = ElevenLabsIntegration()
    
    async def text_to_speech(self, text: str, voice_id: Optional[str] = None) -> Optional[bytes]:
        """
        Convert text to speech using ElevenLabs.
        
        Args:
            text: Text to convert to speech
            voice_id: Optional voice ID to use
            
        Returns:
            Audio data as bytes or None if failed
        """
        try:
            return await self.elevenlabs.text_to_speech(text, voice_id)
            
        except Exception as e:
            logger.error(f"Error generating speech: {str(e)}")
            return None
    
    async def save_audio_to_file(self, audio_data: bytes) -> Optional[str]:
        """
        Save audio data to a temporary file.
        
        Args:
            audio_data: Audio data in binary format
            
        Returns:
            Path to the saved audio file or None if failed
        """
        try:
            if not audio_data:
                return None
                
            temp_file = tempfile.NamedTemporaryFile(suffix=".mp3", delete=False)
            temp_file.write(audio_data)
            temp_file.close()
            
            return temp_file.name
            
        except Exception as e:
            logger.error(f"Error saving audio to file: {str(e)}")
            return None
    
    async def audio_to_base64(self, audio_data: bytes) -> Optional[str]:
        """
        Convert audio data to base64 encoding for web playback.
        
        Args:
            audio_data: Audio data in binary format
            
        Returns:
            Base64 encoded audio string or None if failed
        """
        try:
            if not audio_data:
                return None
                
            base64_audio = base64.b64encode(audio_data).decode("utf-8")
            return f"data:audio/mpeg;base64,{base64_audio}"
            
        except Exception as e:
            logger.error(f"Error converting audio to base64: {str(e)}")
            return None
    
    async def list_available_voices(self) -> List[Dict[str, Any]]:
        """
        Get a list of available voices from ElevenLabs.
        
        Returns:
            List of voice information
        """
        try:
            voices = await self.elevenlabs.get_voices()
            
            # Format voice information for frontend
            formatted_voices = []
            for voice in voices:
                formatted_voices.append({
                    "id": voice.get("voice_id"),
                    "name": voice.get("name"),
                    "preview_url": voice.get("preview_url"),
                    "gender": voice.get("labels", {}).get("gender"),
                    "age": voice.get("labels", {}).get("age"),
                    "accent": voice.get("labels", {}).get("accent"),
                    "use_case": voice.get("labels", {}).get("use_case")
                })
                
            return formatted_voices
            
        except Exception as e:
            logger.error(f"Error listing voices: {str(e)}")
            return []