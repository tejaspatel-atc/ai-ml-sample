from functools import lru_cache
from re import DEBUG
from typing import List, Tuple

from dotenv import load_dotenv
from pydantic_settings import BaseSettings

# Load .env file
load_dotenv()


class Settings(BaseSettings):
    APP_NAME: str = "HelloService Call Handler"
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"
    OPEN_AI_API_KEY: str
    APP_BACKEND_WEBSOCKET_DOMAIN: str

    TWILIO_AUTH_TOKEN: str
    TWILIO_ACCOUNT_SID: str

    SUPABASE_URL: str
    SUPABASE_API_KEY: str

    SAMPLE_RATE: int = 8000
    INTERRUPTION_WORD_COUNT: int = 3
    SILENCE_THRESHOLD: float = 0.2
    DEEPGRAM_SECRET_KEY: str
    DEEPGRAM_ENCODING: str = "mulaw"
    DEEPGRAM_TTS_MODEL: str = "aura-asteria-en"
    DEEPGRAM_SST_MODEL: str = "nova-2"
    SPEECH_DELAY_SECONDS: float = 0

    PUNCTUATION_TERMINATORS: List[str] = [".", "!", "?"]
    OPEN_AI_DELIMITERS: List[str] = [".", "?", "!", ";", ":"]
    SUMMARIZATION_URL: str


@lru_cache()
def get_settings():
    return Settings()


settings = get_settings()
