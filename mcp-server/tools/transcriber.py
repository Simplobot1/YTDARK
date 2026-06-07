import subprocess
import os


def transcribe(video_path: str, language: str = "en") -> str:
    """Transcreve vídeo/áudio usando Whisper local. Retorna texto completo."""
    if not os.path.exists(video_path):
        raise FileNotFoundError(f"Arquivo não encontrado: {video_path}")

    output_dir = os.path.dirname(video_path)

    result = subprocess.run(
        [
            "whisper", video_path,
            "--language", language,
            "--output_format", "txt",
            "--output_dir", output_dir,
            "--model", "base",
        ],
        capture_output=True, text=True, timeout=1800,
    )
    if result.returncode != 0:
        raise RuntimeError(f"Whisper falhou: {result.stderr}")

    base = os.path.splitext(video_path)[0]
    txt_path = base + ".txt"

    if not os.path.exists(txt_path):
        raise RuntimeError(f"Arquivo de transcrição não encontrado: {txt_path}")

    with open(txt_path, "r", encoding="utf-8") as f:
        return f.read().strip()
