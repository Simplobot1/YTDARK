import os
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from app.config import get_settings

SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]
TOKEN_PATH = "credentials/youtube_token.json"


def _get_youtube_service():
    settings = get_settings()
    creds = None
    if os.path.exists(TOKEN_PATH):
        creds = Credentials.from_authorized_user_file(TOKEN_PATH, SCOPES)
    if not creds or not creds.valid:
        flow = InstalledAppFlow.from_client_secrets_file(settings.google_credentials_path, SCOPES)
        creds = flow.run_local_server(port=0)
        os.makedirs(os.path.dirname(TOKEN_PATH), exist_ok=True)
        with open(TOKEN_PATH, "w") as f:
            f.write(creds.to_json())
    return build("youtube", "v3", credentials=creds)


def publicar_video(video_path: str, titulo: str, descricao: str,
                   tags: list, thumbnail_path: str) -> str:
    """Faz upload do vídeo no YouTube. Retorna o link do vídeo publicado."""
    youtube = _get_youtube_service()
    body = {
        "snippet": {
            "title": titulo,
            "description": descricao,
            "tags": tags,
            "categoryId": "27",
        },
        "status": {"privacyStatus": "private"},
    }
    request = youtube.videos().insert(
        part="snippet,status",
        body=body,
        media_body=MediaFileUpload(video_path, chunksize=-1, resumable=True),
    )
    response = request.execute()
    video_id = response["id"]

    if thumbnail_path and os.path.exists(thumbnail_path):
        youtube.thumbnails().set(
            videoId=video_id,
            media_body=MediaFileUpload(thumbnail_path),
        ).execute()

    return f"https://www.youtube.com/watch?v={video_id}"
