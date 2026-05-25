from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    openai_api_key: str = ""
    youtube_api_key: str = ""
    google_credentials_path: str = "credentials/google_credentials.json"
    elevenlabs_api_key: str = ""
    elevenlabs_voice_id: str = ""
    elevenlabs_voice_id_default: str = "2EiwWnXFnvU5JabPnv8n"
    together_ai_key: str = ""
    bg_music_path: str = "assets/bg_music.mp3"
    jwt_secret: str = "dev-secret"
    users: str = "admin@email.com:admin123"
    supabase_url: str = ""
    supabase_anon_key: str = ""
    supabase_service_role_key: str = ""

    class Config:
        env_file = ".env"
        extra = "ignore"

@lru_cache()
def get_settings() -> Settings:
    return Settings()
