import os
import subprocess
import yt_dlp

TEMP_DIR = "temp"

def _ensure_temp():
    os.makedirs(TEMP_DIR, exist_ok=True)

def get_video_metadata(video_url: str) -> dict:
    opts = {"quiet": True, "skip_download": True}
    with yt_dlp.YoutubeDL(opts) as ydl:
        return ydl.extract_info(video_url, download=False) or {}

def download_audio(video_id: str) -> str:
    _ensure_temp()
    out_path = os.path.join(TEMP_DIR, f"{video_id}.mp3")
    if os.path.exists(out_path):
        return out_path
    opts = {
        "format": "bestaudio/best",
        "outtmpl": os.path.join(TEMP_DIR, f"{video_id}.%(ext)s"),
        "postprocessors": [{"key": "FFmpegExtractAudio", "preferredcodec": "mp3"}],
        "quiet": True,
    }
    with yt_dlp.YoutubeDL(opts) as ydl:
        ydl.download([f"https://www.youtube.com/watch?v={video_id}"])
    return out_path

def extract_frames(video_id: str, num_frames: int = 8) -> list:
    _ensure_temp()
    video_path = os.path.join(TEMP_DIR, f"{video_id}.mp4")
    if not os.path.exists(video_path):
        opts = {"format": "best[height<=720]", "outtmpl": video_path, "quiet": True}
        with yt_dlp.YoutubeDL(opts) as ydl:
            ydl.download([f"https://www.youtube.com/watch?v={video_id}"])

    frames_dir = os.path.join(TEMP_DIR, f"{video_id}_frames")
    os.makedirs(frames_dir, exist_ok=True)
    interval = max(1, 60 // num_frames)
    subprocess.run([
        "ffmpeg", "-i", video_path,
        "-vf", f"fps=1/{interval}",
        os.path.join(frames_dir, "frame_%03d.jpg"),
        "-y", "-loglevel", "quiet"
    ], check=True)

    frames = sorted([
        os.path.join(frames_dir, f)
        for f in os.listdir(frames_dir) if f.endswith(".jpg")
    ])
    return frames[:num_frames]

def cleanup_temp(video_id: str):
    import shutil
    for path in [
        os.path.join(TEMP_DIR, f"{video_id}.mp3"),
        os.path.join(TEMP_DIR, f"{video_id}.mp4"),
        os.path.join(TEMP_DIR, f"{video_id}_frames"),
    ]:
        if os.path.isfile(path):
            os.remove(path)
        elif os.path.isdir(path):
            shutil.rmtree(path)
