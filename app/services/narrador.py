import os
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


def gerar_narracao(texto: str, video_id: str) -> str:
    """Gera narração em MP3 com ElevenLabs. Retorna caminho do arquivo."""
    settings = get_settings()
    client = ElevenLabs(api_key=settings.elevenlabs_api_key)
    narration_only = _extract_narration(texto)
    audio = client.generate(
        text=narration_only,
        voice=settings.elevenlabs_voice_id or "Rachel",
        model="eleven_multilingual_v2",
    )
    os.makedirs(TEMP_DIR, exist_ok=True)
    dest = os.path.join(TEMP_DIR, f"{video_id}.mp3")
    with open(dest, "wb") as f:
        for chunk in audio:
            f.write(chunk)
    return dest


def _extract_narration(roteiro: str) -> str:
    """Remove marcações de estrutura, mantém só o texto narrado."""
    lines = []
    for line in roteiro.split("\n"):
        stripped = line.strip()
        if stripped.startswith("[") and stripped.endswith("]"):
            continue
        if stripped:
            lines.append(stripped)
    return " ".join(lines)
