import os
from typing import Optional
from app.config import get_settings


# Try to import ElevenLabs at module load. If the package is not installed
# (e.g. during unit tests), expose a placeholder so `patch("...ElevenLabs")`
# can still find and replace the attribute. The placeholder will raise
# if invoked unmocked.
try:
    from elevenlabs import ElevenLabs  # type: ignore
except ImportError:  # pragma: no cover - exercised only in environments without elevenlabs
    class ElevenLabs:  # type: ignore[no-redef]
        def __init__(self, *_args, **_kwargs):
            raise RuntimeError(
                "elevenlabs package is not installed; install it to call the real API"
            )


TEMP_DIR = "temp"


def gerar_narracao(texto: str, video_id: str, voice_id: Optional[str] = None) -> str:
    """Gera narração em MP3 com ElevenLabs. Retorna caminho do arquivo.

    Args:
        texto: Roteiro a narrar.
        video_id: Identificador (pode ser "canal_id/video_id/narration" para nested paths).
        voice_id: ID da voz no ElevenLabs. Default: settings.elevenlabs_voice_id_default.
    """
    settings = get_settings()
    voz = (
        voice_id
        or settings.elevenlabs_voice_id
        or settings.elevenlabs_voice_id_default
        or "2EiwWnXFnvU5JabPnv8n"
    )
    client = ElevenLabs(api_key=settings.elevenlabs_api_key)
    narration_only = _extract_narration(texto)
    audio = client.generate(
        text=narration_only,
        voice=voz,
        model="eleven_multilingual_v2",
    )
    # Suporta video_id com subpath (ex: "canal/video/narration")
    dest = os.path.join(TEMP_DIR, f"{video_id}.mp3")
    os.makedirs(os.path.dirname(dest) or TEMP_DIR, exist_ok=True)
    with open(dest, "wb") as f:
        for chunk in audio:
            f.write(chunk)
    return dest


def _extract_narration(roteiro: str) -> str:
    """Remove marcações de estrutura ([HOOK], etc), mantém só o texto narrado."""
    lines = []
    for line in roteiro.split("\n"):
        stripped = line.strip()
        if stripped.startswith("[") and stripped.endswith("]"):
            continue
        if stripped:
            lines.append(stripped)
    return " ".join(lines)
