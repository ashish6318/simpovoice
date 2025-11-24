"""
Configuration management for SimploVoice application.
Handles environment variables and application settings.
"""

import os
from dataclasses import dataclass
from typing import Optional
from dotenv import load_dotenv

# Load environment variables at module import time
load_dotenv()


@dataclass
class AIConfig:
    """AI service configuration"""
    groq_api_key: Optional[str]
    model_name: str = "llama3-groq-70b-8192-tool-use-preview"
    max_tokens: int = 200  # Reduced for faster, concise responses
    temperature: float = 0.7
    use_ai: bool = True  # Use AI when available


@dataclass
class DatabaseConfig:
    """Database configuration"""
    db_path: str = "hotel.db"
    backup_enabled: bool = False


@dataclass
class BusinessConfig:
    """Business logic configuration"""
    direct_discount_percentage: int = 15
    currency_symbol: str = "₹"
    min_confidence_threshold: float = 0.5


@dataclass
class SpeechConfig:
    """Speech recognition configuration"""
    default_engine: str = "google"  # google, sphinx, whisper
    timeout: int = 5
    phrase_time_limit: int = 10
    language: str = "en-US"


@dataclass
class TTSConfig:
    """Text-to-Speech configuration"""
    voice_preset: str = "female_professional"  # female_professional, male_professional, female_friendly, male_calm
    voice: str = "en-US-AriaNeural"
    rate: str = "+0%"
    pitch: str = "+0Hz"
    enabled: bool = True
    audio_cache_hours: int = 24  # Auto-cleanup after 24 hours


class Config:
    """Main application configuration"""
    
    def __init__(self):
        self.ai = self._load_ai_config()
        self.database = self._load_database_config()
        self.business = self._load_business_config()
        self.speech = self._load_speech_config()
        self.tts = self._load_tts_config()
    
    def _load_ai_config(self) -> AIConfig:
        """Load AI configuration from environment"""
        api_key = os.getenv("GROQ_API_KEY", "")
        use_ai = bool(api_key and api_key != "PASTE_YOUR_GROQ_KEY_HERE")
        
        return AIConfig(
            groq_api_key=api_key if use_ai else None,
            use_ai=use_ai
        )
    
    def _load_database_config(self) -> DatabaseConfig:
        """Load database configuration"""
        return DatabaseConfig(
            db_path=os.getenv("DB_PATH", "hotel.db"),
            backup_enabled=os.getenv("DB_BACKUP", "false").lower() == "true"
        )
    
    def _load_business_config(self) -> BusinessConfig:
        """Load business logic configuration"""
        return BusinessConfig(
            direct_discount_percentage=int(os.getenv("DIRECT_DISCOUNT", "15")),
            currency_symbol=os.getenv("CURRENCY_SYMBOL", "₹"),
            min_confidence_threshold=float(os.getenv("MIN_CONFIDENCE", "0.5"))
        )
    
    def _load_speech_config(self) -> SpeechConfig:
        """Load speech recognition configuration"""
        return SpeechConfig(
            default_engine=os.getenv("SPEECH_ENGINE", "google"),
            timeout=int(os.getenv("SPEECH_TIMEOUT", "5")),
            phrase_time_limit=int(os.getenv("SPEECH_PHRASE_LIMIT", "10")),
            language=os.getenv("SPEECH_LANGUAGE", "en-US")
        )
    
    def _load_tts_config(self) -> TTSConfig:
        """Load TTS configuration"""
        return TTSConfig(
            voice_preset=os.getenv("TTS_PRESET", "female_professional"),
            voice=os.getenv("TTS_VOICE", "en-US-AriaNeural"),
            rate=os.getenv("TTS_RATE", "+0%"),
            pitch=os.getenv("TTS_PITCH", "+0Hz"),
            enabled=os.getenv("TTS_ENABLED", "true").lower() == "true",
            audio_cache_hours=int(os.getenv("TTS_CACHE_HOURS", "24"))
        )
    
    def is_production(self) -> bool:
        """Check if running in production mode"""
        return os.getenv("ENVIRONMENT", "development").lower() == "production"


# Global configuration instance
config = Config()
