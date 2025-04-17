import os
import logging
from typing import Dict, Any, Optional, List
import httpx
import json
import asyncio
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

logger = logging.getLogger(__name__)

class ElevenLabsIntegration:
    """ElevenLabs integration for text-to-speech synthesis, optimized for high concurrency."""
    
    def __init__(self):
        """Initialize the ElevenLabs integration."""
        self.api_key = os.environ.get("ELEVENLABS_API_KEY")
        self.base_url = "https://api.elevenlabs.io/v1"
        
        if not self.api_key:
            logger.warning("ElevenLabs API key not set. Voice features will not work.")
        
        # Configure connection pool for high concurrency
        # Each agent should handle 10+ concurrent calls
        self.limits = httpx.Limits(
            max_connections=100,  # Dedicated to ElevenLabs
            max_keepalive_connections=20,
            keepalive_expiry=30.0
        )
        
        # Create a shared httpx client with rate limiting
        self.client = None
        
        # Track ongoing requests for load management
        self._ongoing_requests = 0
        self._request_lock = asyncio.Lock()
        
        # Cache for voice settings
        self._voice_settings_cache = {}
        self._voices_cache = None
        self._voices_cache_time = 0
        
    async def _get_client(self) -> httpx.AsyncClient:
        """
        Get or create the httpx client lazily.
        
        Returns:
            httpx.AsyncClient: The client instance
        """
        if self.client is None:
            self.client = httpx.AsyncClient(
                limits=self.limits, 
                timeout=30.0,
                headers={"xi-api-key": self.api_key}
            )
        return self.client
    
    @property
    async def headers(self) -> Dict[str, str]:
        """Get the headers for API requests."""
        return {
            "xi-api-key": self.api_key,
            "Content-Type": "application/json",
            "Accept": "audio/mpeg"
        }
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        retry=retry_if_exception_type((httpx.TimeoutException, httpx.ConnectError))
    )
    async def text_to_speech(
        self, 
        text: str, 
        voice_id: str = None, 
        optimize_streaming_latency: int = 3,
        model_id: str = "eleven_monolingual_v1"
    ) -> Optional[bytes]:
        """
        Convert text to speech using ElevenLabs API.
        
        Args:
            text: Text to convert to speech
            voice_id: Voice ID to use (defaults to ElevenLabs default voice)
            optimize_streaming_latency: Latency optimization level (0-4)
            model_id: Model ID to use for synthesis
            
        Returns:
            Audio data in MP3 format or None if failed
        """
        if not self.api_key:
            raise ValueError("ElevenLabs API key not set")
            
        if not voice_id:
            voice_id = "21m00Tcm4TlvDq8ikWAM"  # Default voice (Rachel)
            
        url = f"{self.base_url}/text-to-speech/{voice_id}"
        
        # Use cached voice settings if available
        if voice_id in self._voice_settings_cache:
            voice_settings = self._voice_settings_cache[voice_id]
        else:
            voice_settings = {
                "stability": 0.5,
                "similarity_boost": 0.75,
                "style": 0.0,
                "use_speaker_boost": True
            }
            # Cache for future use
            self._voice_settings_cache[voice_id] = voice_settings
        
        payload = {
            "text": text,
            "model_id": model_id,
            "voice_settings": voice_settings
        }
        
        # Track ongoing requests to manage load
        async with self._request_lock:
            self._ongoing_requests += 1
        
        try:
            client = await self._get_client()
            # Optimize the payload size
            if len(text) > 1000:
                # For long text, we could consider chunking it, but that's advanced
                logger.warning(f"Converting long text ({len(text)} chars) to speech, may take time")
            
            response = await client.post(
                url,
                json=payload, 
                headers=await self.headers
            )
            response.raise_for_status()
            return response.content
            
        except httpx.HTTPStatusError as e:
            error_detail = e.response.text
            status_code = e.response.status_code
            
            # Handle rate limiting
            if status_code == 429:
                logger.warning(f"ElevenLabs rate limit hit: {error_detail}")
                # Could implement a backoff strategy here
                await asyncio.sleep(2)  # Simple backoff
                # Re-raise to let retry logic handle it
                raise
            
            logger.error(f"ElevenLabs HTTP error {status_code}: {error_detail}")
            return None
            
        except Exception as e:
            logger.error(f"Error generating speech: {str(e)}")
            return None
            
        finally:
            # Decrement ongoing requests counter
            async with self._request_lock:
                self._ongoing_requests -= 1
    
    async def save_audio(self, audio_data: bytes, file_path: str) -> bool:
        """
        Save audio data to a file.
        
        Args:
            audio_data: Audio data in binary format
            file_path: Path to save the audio file
            
        Returns:
            True if successful, False otherwise
        """
        if not audio_data:
            return False
            
        try:
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            with open(file_path, "wb") as f:
                f.write(audio_data)
            return True
        except Exception as e:
            logger.error(f"Error saving audio: {str(e)}")
            return False
    
    async def get_voices(self, force_refresh: bool = False) -> List[Dict[str, Any]]:
        """
        Get available voices from ElevenLabs with caching for performance.
        
        Args:
            force_refresh: Whether to force a refresh of the cache
            
        Returns:
            List of voice information dictionaries
        """
        import time
        
        # Check if we have a cached result that's less than 1 hour old
        current_time = time.time()
        cache_valid = (
            self._voices_cache is not None and 
            current_time - self._voices_cache_time < 3600 and
            not force_refresh
        )
        
        if cache_valid:
            return self._voices_cache
            
        if not self.api_key:
            raise ValueError("ElevenLabs API key not set")
            
        url = f"{self.base_url}/voices"
        
        try:
            client = await self._get_client()
            response = await client.get(url, headers=await self.headers)
            response.raise_for_status()
            data = response.json()
            
            # Update cache
            self._voices_cache = data.get("voices", [])
            self._voices_cache_time = current_time
            
            return self._voices_cache
        except Exception as e:
            logger.error(f"Error getting voices: {str(e)}")
            # Return cached version if available, even if expired
            if self._voices_cache is not None:
                return self._voices_cache
            return []
    
    async def get_voice_settings(self, voice_id: str) -> Dict[str, Any]:
        """
        Get settings for a specific voice with caching.
        
        Args:
            voice_id: Voice ID
            
        Returns:
            Voice settings dictionary
        """
        # Check if we have this in cache
        if voice_id in self._voice_settings_cache:
            return self._voice_settings_cache[voice_id]
            
        if not self.api_key:
            raise ValueError("ElevenLabs API key not set")
            
        url = f"{self.base_url}/voices/{voice_id}/settings"
        
        try:
            client = await self._get_client()
            response = await client.get(url, headers=await self.headers)
            response.raise_for_status()
            settings = response.json()
            
            # Cache the settings
            self._voice_settings_cache[voice_id] = settings
            
            return settings
        except Exception as e:
            logger.error(f"Error getting voice settings: {str(e)}")
            # Return default settings if we can't get specific ones
            default_settings = {
                "stability": 0.5,
                "similarity_boost": 0.75,
                "style": 0.0,
                "use_speaker_boost": True
            }
            return default_settings
            
    async def get_current_load(self) -> Dict[str, int]:
        """
        Get current load statistics.
        
        Returns:
            Dictionary with load information
        """
        async with self._request_lock:
            return {
                "ongoing_requests": self._ongoing_requests
            }
            
    async def close(self):
        """
        Close the httpx client to free resources.
        """
        if self.client:
            await self.client.aclose()
            self.client = None