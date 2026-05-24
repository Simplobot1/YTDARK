import json
import os
from app.models.canal import CanalConfig, ChannelDNA

CANAIS_DIR = "canais"

def listar_canais() -> list:
    if not os.path.exists(CANAIS_DIR):
        return []
    return [d for d in os.listdir(CANAIS_DIR) if os.path.isdir(os.path.join(CANAIS_DIR, d))]

def get_config(canal_id: str) -> CanalConfig:
    path = os.path.join(CANAIS_DIR, canal_id, "config.json")
    with open(path) as f:
        return CanalConfig(**json.load(f))

def save_config(canal_id: str, config: CanalConfig) -> None:
    path = os.path.join(CANAIS_DIR, canal_id, "config.json")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        json.dump(config.model_dump(), f, indent=2, ensure_ascii=False)

def get_dna(canal_id: str) -> ChannelDNA:
    path = os.path.join(CANAIS_DIR, canal_id, "channel_dna.json")
    with open(path) as f:
        return ChannelDNA(**json.load(f))

def save_dna(canal_id: str, dna: ChannelDNA) -> None:
    path = os.path.join(CANAIS_DIR, canal_id, "channel_dna.json")
    with open(path, "w") as f:
        json.dump(dna.model_dump(), f, indent=2, ensure_ascii=False)
