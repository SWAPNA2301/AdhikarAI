"""Voice requests use synthetic WAV recordings and mocked HTTP only."""

import io
import json
import unittest
import wave
from unittest.mock import patch

from adhikar_ai import voice


def wav():
    with io.BytesIO() as stream:
        with wave.open(stream, "wb") as recording:
            recording.setnchannels(1)
            recording.setsampwidth(2)
            recording.setframerate(16000)
            recording.writeframes(b"\0\0" * 16000)
        return stream.getvalue()


class VoiceTests(unittest.TestCase):
    @patch("adhikar_ai.voice.rag.api_key", return_value="fake-secret")
    @patch("adhikar_ai.voice.urlopen")
    def test_transcription_request_and_text(self, request, key):
        request.return_value.__enter__.return_value.read.return_value = json.dumps({"text": " I am a student. "}).encode()
        self.assertEqual(voice.transcribe(wav()), {"text": "I am a student.", "error": ""})
        self.assertIn(b"whisper-large-v3-turbo", request.call_args.args[0].data)
        self.assertNotIn(b"fake-secret", request.call_args.args[0].data)
        self.assertEqual(request.call_args.kwargs["timeout"], 30)

    @patch("adhikar_ai.voice.rag.api_key", return_value="")
    @patch("adhikar_ai.voice.urlopen")
    def test_no_key_does_not_call_provider(self, request, key):
        self.assertTrue(voice.transcribe(wav())["error"])
        request.assert_not_called()

    @patch("adhikar_ai.voice.rag.api_key", return_value="fake-secret")
    @patch("adhikar_ai.voice.urlopen")
    def test_bad_recordings_and_safe_errors(self, request, key):
        for audio in [b"", b"invalid", b"x" * (5 * 1024 * 1024 + 1)]:
            self.assertTrue(voice.transcribe(audio)["error"])
        request.assert_not_called()
        request.side_effect = RuntimeError("fake-secret")
        result = voice.transcribe(wav())
        self.assertEqual(result["text"], "")
        self.assertNotIn("fake-secret", str(result))

    @patch("adhikar_ai.voice.rag.api_key", return_value="fake-secret")
    @patch("adhikar_ai.voice.urlopen")
    def test_invalid_provider_output(self, request, key):
        for output in [b"not json", b'{"text": null}', b'{"text": ""}']:
            request.return_value.__enter__.return_value.read.return_value = output
            self.assertTrue(voice.transcribe(wav())["error"])

