"""Explicit, bounded voice transcription; recordings are never written to disk."""

import io
import json
import uuid
import wave
from urllib.request import Request, urlopen

from adhikar_ai import rag


def transcribe(audio):
    """Send a short WAV recording only on explicit UI submission."""
    key = rag.api_key()
    if not key:
        return {"text": "", "error": "Voice transcription needs GROQ_API_KEY. You can still type your details."}
    if not audio or len(audio) > 5 * 1024 * 1024:
        return {"text": "", "error": "Record audio up to 5 MB and two minutes."}
    try:
        with wave.open(io.BytesIO(audio)) as recording:
            if not 0 < recording.getnframes() / recording.getframerate() <= 120:
                return {"text": "", "error": "Record between one second and two minutes of audio."}
    except Exception:
        return {"text": "", "error": "The recording could not be read. Please record again."}
    boundary = uuid.uuid4().hex
    body = (
        f"--{boundary}\r\nContent-Disposition: form-data; name=\"model\"\r\n\r\n"
        f"whisper-large-v3-turbo\r\n--{boundary}\r\n"
        'Content-Disposition: form-data; name="response_format"\r\n\r\njson\r\n'
        f"--{boundary}\r\nContent-Disposition: form-data; name=\"file\"; filename=\"recording.wav\"\r\n"
        "Content-Type: audio/wav\r\n\r\n"
    ).encode() + audio + f"\r\n--{boundary}--\r\n".encode()
    try:
        request = Request(
            "https://api.groq.com/openai/v1/audio/transcriptions", data=body,
            headers={"Authorization": "Bearer " + key,
                     "Content-Type": "multipart/form-data; boundary=" + boundary},
            method="POST",
        )
        with urlopen(request, timeout=30) as response:
            raw = response.read(65537)
        if len(raw) > 65536:
            raise ValueError()
        text = json.loads(raw)["text"]
        if not isinstance(text, str) or not text.strip() or len(text) > 10000:
            raise ValueError()
        return {"text": text.strip(), "error": ""}
    except Exception:
        return {"text": "", "error": "Transcription is unavailable. Please retry or type your details."}

