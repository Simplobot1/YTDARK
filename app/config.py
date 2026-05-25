from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    openai_api_key: str = ""
    youtube_api_key: str = ""
    google_credentials_path: str = "credentials/google_credentials.json"
    elevenlabs_api_key: str = ""
    elevenlabs_voice_id: str = ""
    shotstack_api_key: str = ""
    shotstack_env: str = "v1"
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
