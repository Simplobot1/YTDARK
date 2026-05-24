import os
import httpx
from app.config import get_settings
from app.models.canal import ChannelDNA

TEMP_DIR = "temp"


# Try to import OpenAI at module load. If the package is not installed
# (e.g. during unit tests), expose a placeholder so `patch("...OpenAI")`
# can still find and replace the attribute. The placeholder will raise
# if invoked unmocked.
try:
    from openai import OpenAI  # type: ignore
except ImportError:  # pragma: no cover - exercised only in environments without openai
    class OpenAI:  # type: ignore[no-redef]
        def __init__(self, *_args, **_kwargs):
            raise RuntimeError(
                "openai package is not installed; install it to call the real API"
            )


def gerar_thumbnail(titulo: str, dna: ChannelDNA, video_id: str) -> str:
    """Gera thumbnail original com DALL-E 3. Retorna caminho do arquivo."""
    client = OpenAI(api_key=get_settings().openai_api_key)
    cores = " and ".join(dna.paleta_cores[:2])
    prompt = (
        f"YouTube thumbnail for a video titled '{titulo}'. "
        f"Style: {dna.thumbnail_formula}. "
        f"Colors: {cores}. "
        f"Font style: {dna.thumbnail_fonte}. "
        f"Clean, professional, high contrast. No text overlays. "
        f"Finance/money visual theme. 16:9 aspect ratio."
    )
    response = client.images.generate(
        model="dall-e-3",
        prompt=prompt,
        size="1792x1024",
        quality="standard",
        n=1,
    )
    image_url = response.data[0].url
    os.makedirs(TEMP_DIR, exist_ok=True)
    dest = os.path.join(TEMP_DIR, f"{video_id}_thumbnail.jpg")
    with httpx.Client() as c:
        r = c.get(image_url)
        with open(dest, "wb") as f:
            f.write(r.content)
    return dest
