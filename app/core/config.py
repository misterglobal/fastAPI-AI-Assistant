from pydantic_settings import BaseSettings
from pydantic import PostgresDsn
from typing import Optional, Dict, Any, List
import os
import json

class Settings(BaseSettings):
    """Application settings that can be loaded from environment variables."""

    # API configuration
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "AI Phone Assistant"

    # Supabase configuration
    SUPABASE_URL: str = os.environ.get("SUPABASE_URL", "")
    SUPABASE_KEY: str = os.environ.get("SUPABASE_KEY", "")
    SESSION_ID: str = os.environ.get("SESSION_ID", "")

    # OAuth and JWT
    JWT_SECRET: str = os.environ.get("JWT_SECRET", "")  # Must be set in environment
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION_SECONDS: int = 3600

    # Postgres (for SQLAlchemy, if needed)
    POSTGRES_SERVER: str = os.environ.get("POSTGRES_SERVER", "localhost")
    POSTGRES_USER: str = os.environ.get("POSTGRES_USER", "")
    POSTGRES_PASSWORD: str = os.environ.get("POSTGRES_PASSWORD", "")
    POSTGRES_DB: str = os.environ.get("POSTGRES_DB", "ai_phone_assistant")
    SQLALCHEMY_DATABASE_URI: Optional[PostgresDsn] = None

    # Twilio configuration
    TWILIO_ACCOUNT_SID: str = os.environ.get("TWILIO_ACCOUNT_SID", "")
    TWILIO_AUTH_TOKEN: str = os.environ.get("TWILIO_AUTH_TOKEN", "")
    TWILIO_PHONE_NUMBER: str = os.environ.get("TWILIO_PHONE_NUMBER", "")

    # OpenAI configuration
    OPENAI_API_KEY: str = os.environ.get("OPENAI_API_KEY", "")
    OPENAI_MODEL: str = os.environ.get("OPENAI_MODEL", "gpt-4-turbo")
    OPENAI_EMBEDDING_MODEL: str = os.environ.get("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small")

    # ElevenLabs configuration
    ELEVENLABS_API_KEY: str = os.environ.get("ELEVENLABS_API_KEY", "")
    ELEVENLABS_DEFAULT_VOICE: str = os.environ.get("ELEVENLABS_DEFAULT_VOICE", "")

    # Google API configuration
    GOOGLE_CLIENT_ID: str = os.environ.get("GOOGLE_CLIENT_ID", "")
    GOOGLE_CLIENT_SECRET: str = os.environ.get("GOOGLE_CLIENT_SECRET", "")
    GOOGLE_REDIRECT_URI: str = os.environ.get("GOOGLE_REDIRECT_URI", "")

    # Application configuration
    FRONTEND_URL: str = os.environ.get("FRONTEND_URL", "http://localhost:3000")
    BASE_URL: str = os.environ.get("BASE_URL", "http://localhost:8000")

    # Performance configuration
    MAX_CONCURRENT_CALLS_PER_AGENT: int = int(os.environ.get("MAX_CONCURRENT_CALLS_PER_AGENT", "10"))
    MAX_CONNECTIONS: int = int(os.environ.get("MAX_CONNECTIONS", "500"))
    MAX_KEEPALIVE_CONNECTIONS: int = int(os.environ.get("MAX_KEEPALIVE_CONNECTIONS", "100"))

    # Default business hours configuration
    DEFAULT_BUSINESS_HOURS: Dict[str, Any] = {
        "monday": {"start": "09:00", "end": "17:00", "active": True},
        "tuesday": {"start": "09:00", "end": "17:00", "active": True},
        "wednesday": {"start": "09:00", "end": "17:00", "active": True},
        "thursday": {"start": "09:00", "end": "17:00", "active": True},
        "friday": {"start": "09:00", "end": "17:00", "active": True},
        "saturday": {"start": "09:00", "end": "17:00", "active": False},
        "sunday": {"start": "09:00", "end": "17:00", "active": False}
    }

    # Default system prompts by industry
    DEFAULT_SYSTEM_PROMPTS: Dict[str, str] = {
        "general": "You are an AI assistant answering a phone call. Be helpful, concise, and professional. Ask questions to better understand caller needs.",
        "healthcare": "You are an AI assistant for a healthcare provider. Be professional and compassionate. Collect patient information, but never provide medical advice. Direct urgent issues to call 911.",
        "retail": "You are an AI assistant for a retail business. Help customers with product information, store hours, and order status. Be friendly and helpful.",
        "restaurant": "You are an AI assistant for a restaurant. You can take reservations, provide menu information, and answer questions about hours and location.",
        "professional_services": "You are an AI assistant for a professional services firm. Be polite and professional while gathering information about the caller's needs."
    }

    # Rate limits for API protection (requests per minute)
    RATE_LIMITS: Dict[str, int] = {
        "calls": 60,     # 60 call-related API requests per minute
        "sms": 120,      # 120 SMS-related API requests per minute
        "calendar": 300, # 300 calendar-related API requests per minute
        "default": 600   # 600 API requests per minute for all other endpoints
    }

    model_config = {
        "case_sensitive": True,
        "env_file": ".env",
    }

    @classmethod
    def parse_env_var(cls, field_name: str, raw_val: str) -> Any:
        if field_name == "DEFAULT_BUSINESS_HOURS":
            return json.loads(raw_val)
        return raw_val

    def get_system_prompt(self, industry_type: str = "general") -> str:
        """Get a default system prompt for a specific industry."""
        return self.DEFAULT_SYSTEM_PROMPTS.get(industry_type, self.DEFAULT_SYSTEM_PROMPTS["general"])

    def get_business_hours(self) -> Dict[str, Any]:
        """Get the default business hours configuration."""
        return self.DEFAULT_BUSINESS_HOURS

    def get_concurrency_settings(self) -> Dict[str, int]:
        """Get the concurrency settings for the application."""
        return {
            "max_concurrent_calls_per_agent": self.MAX_CONCURRENT_CALLS_PER_AGENT,
            "max_connections": self.MAX_CONNECTIONS,
            "max_keepalive_connections": self.MAX_KEEPALIVE_CONNECTIONS
        }

settings = Settings()