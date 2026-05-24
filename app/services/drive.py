import os
import io
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload
from google.oauth2.service_account import Credentials
from app.config import get_settings

SCOPES = ["https://www.googleapis.com/auth/drive"]

def _get_service():
    settings = get_settings()
    creds = Credentials.from_service_account_file(settings.google_credentials_path, scopes=SCOPES)
    return build("drive", "v3", credentials=creds)

def upload_file(local_path: str, drive_folder_id: str, mime_type: str = "application/octet-stream") -> str:
    service = _get_service()
    file_metadata = {"name": os.path.basename(local_path), "parents": [drive_folder_id]}
    media = MediaFileUpload(local_path, mimetype=mime_type, resumable=True)
    file = service.files().create(body=file_metadata, media_body=media, fields="id").execute()
    file_id = file.get("id")
    service.permissions().create(
        fileId=file_id, body={"type": "anyone", "role": "reader"}
    ).execute()
    return f"https://drive.google.com/file/d/{file_id}/view"

def download_file(file_id: str, dest_path: str) -> str:
    service = _get_service()
    request = service.files().get_media(fileId=file_id)
    with io.FileIO(dest_path, "wb") as f:
        downloader = MediaIoBaseDownload(f, request)
        done = False
        while not done:
            _, done = downloader.next_chunk()
    return dest_path

def get_folder_id_from_link(link: str) -> str:
    return link.split("/d/")[1].split("/")[0]
