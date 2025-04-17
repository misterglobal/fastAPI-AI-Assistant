import os
import logging
from typing import Dict, Any, Optional, List
import openai
import json

logger = logging.getLogger(__name__)

class OpenAIIntegration:
    """OpenAI integration for AI and NLP functions."""

    def __init__(self):
        """Initialize the OpenAI integration."""
        self.api_key = os.environ.get("OPENAI_API_KEY")
        
        if not self.api_key:
            logger.warning("OpenAI API key not set. AI features will not work.")
        else:
            openai.api_key = self.api_key
        
        # Default model settings
        self.chat_model = "gpt-4-turbo"
        self.embedding_model = "text-embedding-3-small"
        self.whisper_model = "whisper-1"

    async def generate_response(self, messages: List[Dict], system_prompt: str = None, max_tokens: int = 500) -> str:
        """
        Generate a response using the OpenAI API.
        
        Args:
            messages: List of message dictionaries
            system_prompt: Optional system prompt to guide the model
            max_tokens: Maximum tokens in the response
            
        Returns:
            Generated text response
        """
        if not self.api_key:
            raise ValueError("OpenAI API key not set")
            
        try:
            # Add system prompt if provided
            if system_prompt:
                full_messages = [{"role": "system", "content": system_prompt}]
                full_messages.extend(messages)
            else:
                full_messages = messages
                
            response = await openai.ChatCompletion.acreate(
                model=self.chat_model,
                messages=full_messages,
                max_tokens=max_tokens,
                temperature=0.7,
            )
            
            return response.choices[0].message.content.strip()
        except Exception as e:
            logger.error(f"Error generating OpenAI response: {str(e)}")
            raise

    async def transcribe_audio(self, audio_url: str) -> Dict[str, Any]:
        """
        Transcribe audio using Whisper API.
        
        Args:
            audio_url: URL of the audio file
            
        Returns:
            Transcription result
        """
        if not self.api_key:
            raise ValueError("OpenAI API key not set")
            
        try:
            # Download the audio file
            async with openai.AsyncHttpClient().get(audio_url) as response:
                audio_content = await response.read()
                
            # Transcribe the audio
            response = await openai.Audio.atranscribe(
                model=self.whisper_model,
                file=("audio.wav", audio_content)
            )
            
            return {
                "text": response.text,
                "confidence": getattr(response, "confidence", None)
            }
        except Exception as e:
            logger.error(f"Error transcribing audio: {str(e)}")
            raise
            
    async def analyze_conversation(self, transcript: str, prompt: str = None) -> Dict[str, Any]:
        """
        Analyze conversation transcript for insights.
        
        Args:
            transcript: Conversation transcript
            prompt: Optional custom prompt for analysis
            
        Returns:
            Analysis results
        """
        if not self.api_key:
            raise ValueError("OpenAI API key not set")
            
        try:
            # Default analysis prompt if not provided
            if not prompt:
                prompt = """
                Analyze the following conversation transcript between an AI assistant and a caller.
                Please provide:
                1. A brief summary of the conversation
                2. Key points discussed
                3. Any action items or follow-ups needed
                4. The caller's sentiment (positive, neutral, negative)
                
                Format your response as JSON with these fields.
                
                Transcript:
                """
                
            messages = [
                {"role": "system", "content": "You are an expert conversation analyst. Extract key information and format as JSON."},
                {"role": "user", "content": f"{prompt}\n\n{transcript}"}
            ]
            
            response = await openai.ChatCompletion.acreate(
                model=self.chat_model,
                messages=messages,
                response_format={"type": "json_object"},
                temperature=0.3,
                max_tokens=1000
            )
            
            try:
                analysis = json.loads(response.choices[0].message.content)
                return analysis
            except json.JSONDecodeError:
                # Fallback if the response isn't valid JSON
                return {
                    "summary": response.choices[0].message.content.strip(),
                    "error": "Could not parse as JSON"
                }
                
        except Exception as e:
            logger.error(f"Error analyzing conversation: {str(e)}")
            raise
            
    async def create_embeddings(self, text: str) -> List[float]:
        """
        Create embeddings for text.
        
        Args:
            text: Input text
            
        Returns:
            Vector embeddings
        """
        if not self.api_key:
            raise ValueError("OpenAI API key not set")
            
        try:
            response = await openai.Embedding.acreate(
                model=self.embedding_model,
                input=text
            )
            
            return response.data[0].embedding
        except Exception as e:
            logger.error(f"Error creating embeddings: {str(e)}")
            raise