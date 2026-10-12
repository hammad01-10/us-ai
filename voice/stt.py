import logging
import sounddevice as sd
import numpy as np
import torch
from faster_whisper import WhisperModel

_WHISPER_INSTANCE = None


def get_whisper_model(model_size="base", device=None, compute_type=None):
    """
    Returns a cached WhisperModel singleton.
    Avoids expensive model reloads on every spoken turn.
    """
    global _WHISPER_INSTANCE
    if _WHISPER_INSTANCE is None:
        if device is None:
            device = "cuda" if torch.cuda.is_available() else "cpu"
        if compute_type is None:
            compute_type = "float16" if device == "cuda" else "int8"

        logging.info(f"Loading WhisperModel: model={model_size}, device={device}, compute_type={compute_type}")
        _WHISPER_INSTANCE = WhisperModel(
            model_size,
            device=device,
            compute_type=compute_type,
        )
    return _WHISPER_INSTANCE


def transcribe_audio(audio, whisper_model=None, language="en"):
    """
    Transcribes audio array to string using the cached Whisper model.
    """
    if audio is None or len(audio) == 0:
        return ""

    model = whisper_model or get_whisper_model()
    segments, _ = model.transcribe(
        audio,
        language=language,
        beam_size=1,
        temperature=0,
        vad_filter=False,
        condition_on_previous_text=False,
    )
    text = " ".join(
        segment.text.strip()
        for segment in segments
        if segment.text.strip()
    )
    return text.strip()


def record_and_transcribe(duration=5, sample_rate=16000, device=None):
    """
    Records audio for a fixed duration and transcribes it.
    """
    print("\nListening...")
    audio = sd.rec(
        int(duration * sample_rate),
        samplerate=sample_rate,
        channels=1,
        dtype="float32",
        device=device,
    )
    sd.wait()
    print("Processing speech...")
    audio = audio.flatten()
    return transcribe_audio(audio)
