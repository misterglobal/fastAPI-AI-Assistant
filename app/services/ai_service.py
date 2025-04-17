import os
import logging
from typing import Dict, Optional, List, Any, Union
import uuid

from app.integrations.openai_integration import OpenAIIntegration

logger = logging.getLogger(__name__)

class AIService:
    """Service for AI-related functionality."""
    
    def __init__(self):
        """Initialize the AI service."""
        self.openai = OpenAIIntegration()
    
    async def generate_completion(self, prompt: str, system_message: str = None, max_tokens: int = 500) -> str:
        """
        Generate a completion using OpenAI.
        
        Args:
            prompt: User prompt
            system_message: Optional system message
            max_tokens: Maximum tokens in response
            
        Returns:
            Generated text
        """
        try:
            messages = [{"role": "user", "content": prompt}]
            return await self.openai.generate_response(messages, system_prompt=system_message, max_tokens=max_tokens)
            
        except Exception as e:
            logger.error(f"Error generating AI completion: {str(e)}")
            raise
    
    async def generate_chat_response(self, conversation_history: List[Dict[str, str]], system_message: str = None) -> str:
        """
        Generate a response based on conversation history.
        
        Args:
            conversation_history: List of conversation messages
            system_message: Optional system message
            
        Returns:
            Generated response
        """
        try:
            return await self.openai.generate_response(conversation_history, system_prompt=system_message)
            
        except Exception as e:
            logger.error(f"Error generating chat response: {str(e)}")
            raise
    
    async def transcribe_audio_file(self, audio_file_path: str) -> Optional[Dict[str, Any]]:
        """
        Transcribe an audio file.
        
        Args:
            audio_file_path: Path to audio file
            
        Returns:
            Transcription results
        """
        try:
            # Check if file exists
            if not os.path.exists(audio_file_path):
                logger.error(f"Audio file not found: {audio_file_path}")
                return None
                
            # Create a file URL (this is a simplified approach, real-world would use storage)
            file_url = f"file://{audio_file_path}"
            
            return await self.openai.transcribe_audio(file_url)
            
        except Exception as e:
            logger.error(f"Error transcribing audio: {str(e)}")
            return None
    
    async def summarize_text(self, text: str, max_length: int = 200) -> str:
        """
        Summarize text to a specified maximum length.
        
        Args:
            text: Text to summarize
            max_length: Maximum length of summary
            
        Returns:
            Summarized text
        """
        try:
            system_prompt = f"Summarize the following text concisely in {max_length} characters or less:"
            messages = [{"role": "user", "content": text}]
            
            return await self.openai.generate_response(messages, system_prompt=system_prompt, max_tokens=max_length // 4)
            
        except Exception as e:
            logger.error(f"Error summarizing text: {str(e)}")
            raise
    
    async def generate_system_prompt(self, business_type: str, tone: str = "professional") -> str:
        """
        Generate a system prompt for a specific business type and tone.
        
        Args:
            business_type: Type of business
            tone: Communication tone
            
        Returns:
            Generated system prompt
        """
        try:
            prompt = f"""Create a system prompt for an AI assistant that answers the phone for a {business_type} business.
            The tone should be {tone}. Include instructions for how to handle common inquiries, 
            scheduling, and basic information requests. The AI should be professional but friendly, 
            and should know to gather appropriate information from callers. Do not format as a list 
            of rules, but as a coherent paragraph of instructions."""
            
            messages = [{"role": "user", "content": prompt}]
            
            return await self.openai.generate_response(messages, max_tokens=800)
            
        except Exception as e:
            logger.error(f"Error generating system prompt: {str(e)}")
            raise