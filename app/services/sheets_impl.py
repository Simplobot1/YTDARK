import json
from typing import List, Optional
from datetime import datetime
import gspread
from google.oauth2.service_account import Credentials
from app.services.db import DatabaseInterface
from app.models.video import Video, VideoStatus
from app.models.canal_candidato import CanalCandidato, MetricasCanal
from app.config import get_settings

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

class SheetsDatabase(DatabaseInterface):
    def __init__(self, sheets_id: str):
        settings = get_settings()
        creds = Credentials.from_service_account_file(settings.google_credentials_path, scopes=SCOPES)
        self.client = gspread.authorize(creds)
        self.sheet = self.client.open_by_key(sheets_id)

    def _get_or_create_tab(self, nome: str, headers: List[str]):
        try:
            return self.sheet.worksheet(nome)
        except gspread.WorksheetNotFound:
            ws = self.sheet.add_worksheet(title=nome, rows=1000, cols=len(headers))
            ws.append_row(headers)
            return ws

    def salvar_video(self, canal_id: str, video: Video) -> None:
        ws = self._get_or_create_tab("Pipeline", [
            "video_id","titulo","canal_fonte","views","data_pub",
            "tipo","score","status","transcricao","drive_link","yt_link"
        ])
        ws.append_row([
            video.video_id, video.titulo, video.canal_fonte, video.views,
            video.data_pub, video.tipo, video.score, video.status.value,
            video.transcricao or "", video.drive_link or "", video.yt_link or ""
        ])

    def listar_candidatos(self, canal_id: str) -> List[Video]:
        ws = self._get_or_create_tab("Pipeline", [
            "video_id","titulo","canal_fonte","views","data_pub",
            "tipo","score","status","transcricao","drive_link","yt_link"
        ])
        records = ws.get_all_records()
        result = []
        for r in records:
            try:
                result.append(Video(
                    video_id=str(r["video_id"]), titulo=str(r["titulo"]),
                    canal_fonte=str(r["canal_fonte"]), views=int(r["views"]),
                    data_pub=str(r["data_pub"]), tipo=str(r["tipo"]),
                    score=float(r["score"]), status=VideoStatus(r["status"]),
                    transcricao=r.get("transcricao") or None,
                    drive_link=r.get("drive_link") or None,
                    yt_link=r.get("yt_link") or None,
                    duracao_min=0.0
                ))
            except Exception:
                continue
        return result

    def atualizar_status(self, canal_id: str, video_id: str, status: VideoStatus) -> None:
        try:
            ws = self.sheet.worksheet("Pipeline")
        except gspread.WorksheetNotFound:
            return
        records = ws.get_all_records()
        for i, r in enumerate(records, start=2):
            if str(r["video_id"]) == video_id:
                cell = ws.find("status")
                if cell:
                    ws.update_cell(i, cell.col, status.value)
                return

    def atualizar_video(self, canal_id: str, video: Video) -> None:
        self.atualizar_status(canal_id, video.video_id, video.status)

    def buscar_video(self, canal_id: str, video_id: str) -> Optional[Video]:
        return next((v for v in self.listar_candidatos(canal_id) if v.video_id == video_id), None)

    def salvar_candidato_canal(self, canal_id: str, candidato: CanalCandidato) -> None:
        ws = self._get_or_create_tab("Canais Candidatos", [
            "handle","nome","channel_id","subscribers","avg_views",
            "engagement_rate","upload_freq","avg_duration","momentum","score","adicionado"
        ])
        ws.append_row([
            candidato.handle, candidato.nome, candidato.channel_id,
            candidato.metricas.subscribers, candidato.metricas.avg_views,
            candidato.metricas.engagement_rate, candidato.metricas.upload_freq_mensal,
            candidato.metricas.avg_duration_min, candidato.metricas.momentum,
            candidato.score, str(candidato.adicionado)
        ])

    def listar_candidatos_canal(self, canal_id: str) -> List[CanalCandidato]:
        try:
            ws = self.sheet.worksheet("Canais Candidatos")
        except gspread.WorksheetNotFound:
            return []
        records = ws.get_all_records()
        result = []
        for r in records:
            try:
                result.append(CanalCandidato(
                    handle=r["handle"], nome=r["nome"], channel_id=r["channel_id"],
                    metricas=MetricasCanal(
                        subscribers=int(r["subscribers"]), avg_views=float(r["avg_views"]),
                        engagement_rate=float(r["engagement_rate"]),
                        upload_freq_mensal=float(r["upload_freq"]),
                        avg_duration_min=float(r["avg_duration"]),
                        momentum=r["momentum"]
                    ),
                    score=float(r["score"]),
                    adicionado=str(r["adicionado"]) == "True"
                ))
            except Exception:
                continue
        return result

    def salvar_keyword(self, canal_id: str, termo: str, volume: int, competition: float, seo_score: float) -> None:
        ws = self._get_or_create_tab("Keywords", ["termo","volume","competition","seo_score","data"])
        ws.append_row([termo, volume, competition, seo_score, datetime.now().strftime("%Y-%m-%d")])
