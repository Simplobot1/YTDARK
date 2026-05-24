import whisper
import os

_model = None

def _get_model():
    global _model
    if _model is None:
        _model = whisper.load_model("base")
    return _model

def transcrever(audio_path: str, idioma: str = "en") -> str:
    model = _get_model()
    result = model.transcribe(audio_path, language=idioma, fp16=False)
    return result["text"].strip()
