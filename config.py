import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config:
    """Configuration class for the voice chatbot application."""

    # Gemini API Configuration
    GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
    GEMINI_BASE_URL = "https://generativelanguage.googleapis.com/v1beta"
    GEMINI_MODEL = os.getenv('GEMINI_MODEL', 'gemini-2.0-flash')

    # Audio Configuration
    AUDIO_SAMPLE_RATE = int(os.getenv('AUDIO_SAMPLE_RATE', 44100))
    AUDIO_CHUNK_SIZE = int(os.getenv('AUDIO_CHUNK_SIZE', 1024))
    AUDIO_FORMAT = int(os.getenv('AUDIO_FORMAT', 16))
    AUDIO_CHANNELS = int(os.getenv('AUDIO_CHANNELS', 1))

    # Recording Configuration
    MAX_RECORDING_DURATION = int(os.getenv('MAX_RECORDING_DURATION', 30))
    SILENCE_THRESHOLD = int(os.getenv('SILENCE_THRESHOLD', 500))
    SILENCE_DURATION = int(os.getenv('SILENCE_DURATION', 2))

    # TTS Configuration
    TTS_ENGINE = os.getenv('TTS_ENGINE', 'pyttsx3')
    TTS_RATE = int(os.getenv('TTS_RATE', 200))
    TTS_VOLUME = float(os.getenv('TTS_VOLUME', 0.9))

    # Application Configuration
    DEBUG = os.getenv('DEBUG', 'True').lower() == 'true'
    SECRET_KEY = os.getenv('SECRET_KEY', 'your-secret-key-here')

    @classmethod
    def validate_config(cls):
        """Validate that all required configuration is present."""
        if not cls.GEMINI_API_KEY:
            raise ValueError("GEMINI_API_KEY is required")
        print("Configuration loaded successfully!")
        return True