import subprocess
import json
import os


def extract_frames(video_path: str, n_frames: int = 10) -> list[str]:
    """Extrai n_frames distribuídos uniformemente do vídeo. Retorna lista de caminhos."""
    if not os.path.exists(video_path):
        raise FileNotFoundError(f"Arquivo não encontrado: {video_path}")

    base = os.path.splitext(video_path)[0]
    output_dir = base + "_frames"
    os.makedirs(output_dir, exist_ok=True)

    probe = subprocess.run(
        [
            "ffprobe", "-v", "quiet",
            "-print_format", "json",
            "-show_format",
            video_path,
        ],
        capture_output=True, text=True, timeout=30,
    )
    if probe.returncode != 0:
        raise RuntimeError(f"ffprobe falhou: {probe.stderr}")

    info = json.loads(probe.stdout)
    duration = float(info["format"]["duration"])

    frame_paths = []
    for i in range(n_frames):
        timestamp = (duration / n_frames) * i
        output_path = os.path.join(output_dir, f"frame_{i:04d}.jpg")
        subprocess.run(
            [
                "ffmpeg", "-ss", str(timestamp),
                "-i", video_path,
                "-frames:v", "1",
                "-q:v", "2",
                output_path, "-y",
            ],
            capture_output=True, timeout=30,
        )
        if os.path.exists(output_path):
            frame_paths.append(output_path)

    return frame_paths
