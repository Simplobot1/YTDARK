import json, os
from typing import List, Optional
from datetime import date
from app.services.db import DatabaseInterface
from app.models.video import Video, VideoStatus
from app.models.canal_candidato import CanalCandidato, MetricasCanal

CANAIS_DIR = os.environ.get("CANAIS_DIR", "canais")

def _path(canal_id: str) -> str:
    d = os.path.join(CANAIS_DIR, canal_id)
    os.makedirs(d, exist_ok=True)
    return os.path.join(d, "videos.json")

def _load(canal_id: str) -> List[dict]:
    p = _path(canal_id)
    if not os.path.exists(p):
        return []
    try:
        with open(p, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []

def _save(canal_id: str, records: List[dict]) -> None:
    with open(_path(canal_id), "w", encoding="utf-8") as f:
        json.dump(records, f, ensure_ascii=False, indent=2)

class FileDatabase(DatabaseInterface):
    def salvar_video(self, canal_id: str, video: Video) -> None:
        records = _load(canal_id)
        data = video.model_dump()
        data["status"] = video.status.value
        for i, r in enumerate(records):
            if r.get("video_id") == video.video_id:
                records[i] = data
                _save(canal_id, records)
                return
        records.append(data)
        _save(canal_id, records)

    def listar_candidatos(self, canal_id: str) -> List[Video]:
        result = []
        for r in _load(canal_id):
            try:
                r = dict(r)
                r["status"] = VideoStatus(r.get("status", "candidato"))
                result.append(Video(**r))
            except Exception:
                continue
        return result

    def atualizar_status(self, canal_id: str, video_id: str, status: VideoStatus) -> None:
        records = _load(canal_id)
        for r in records:
            if r.get("video_id") == video_id:
                r["status"] = status.value
                break
        _save(canal_id, records)

    def atualizar_video(self, canal_id: str, video: Video) -> None:
        records = _load(canal_id)
        data = video.model_dump()
        data["status"] = video.status.value
        for i, r in enumerate(records):
            if r.get("video_id") == video.video_id:
                records[i] = data
                _save(canal_id, records)
                return

    def buscar_video(self, canal_id: str, video_id: str) -> Optional[Video]:
        return next((v for v in self.listar_candidatos(canal_id) if v.video_id == video_id), None)

    def salvar_candidato_canal(self, canal_id: str, candidato: CanalCandidato) -> None:
        p = os.path.join(CANAIS_DIR, canal_id, "canais_candidatos.json")
        records = []
        if os.path.exists(p):
            try:
                with open(p, "r", encoding="utf-8") as f:
                    records = json.load(f)
            except Exception:
                pass
        data = candidato.model_dump()
        for i, r in enumerate(records):
            if r.get("handle") == candidato.handle:
                records[i] = data
                break
        else:
            records.append(data)
        os.makedirs(os.path.dirname(p), exist_ok=True)
        with open(p, "w", encoding="utf-8") as f:
            json.dump(records, f, ensure_ascii=False, indent=2)

    def listar_candidatos_canal(self, canal_id: str) -> List[CanalCandidato]:
        p = os.path.join(CANAIS_DIR, canal_id, "canais_candidatos.json")
        if not os.path.exists(p):
            return []
        try:
            with open(p, "r", encoding="utf-8") as f:
                records = json.load(f)
        except Exception:
            return []
        result = []
        for r in records:
            try:
                m = r.get("metricas", {})
                result.append(CanalCandidato(
                    handle=r["handle"], nome=r["nome"], channel_id=r["channel_id"],
                    metricas=MetricasCanal(**m) if isinstance(m, dict) else m,
                    score=r.get("score", 0.0),
                    melhor_video_recente=r.get("melhor_video_recente"),
                    adicionado=r.get("adicionado", False),
                ))
            except Exception:
                continue
        return result

    def salvar_keyword(self, canal_id: str, termo: str, volume: int, competition: float, seo_score: float) -> None:
        p = os.path.join(CANAIS_DIR, canal_id, "keywords.json")
        records = []
        if os.path.exists(p):
            try:
                with open(p, "r", encoding="utf-8") as f:
                    records = json.load(f)
            except Exception:
                pass
        entry = {"termo": termo, "volume": volume, "competition": competition,
                 "seo_score": seo_score, "data": str(date.today())}
        for i, r in enumerate(records):
            if r.get("termo") == termo:
                records[i] = entry
                break
        else:
            records.append(entry)
        os.makedirs(os.path.dirname(p), exist_ok=True)
        with open(p, "w", encoding="utf-8") as f:
            json.dump(records, f, ensure_ascii=False, indent=2)
