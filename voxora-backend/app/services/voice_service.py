"""
Voxora Backend — Google Cloud Voice Service (STT & TTS).

Provides Speech-to-Text and Text-to-Speech integration with Google Cloud
and graceful fallback handling.
"""

import asyncio
import logging
import os
from google.cloud import texttospeech, speech
from app.config import get_settings

logger = logging.getLogger(__name__)


class VoiceService:
    """Server-side voice processing using Google Cloud."""

    def __init__(self) -> None:
        self.settings = get_settings()

    def _get_tts_client(self) -> texttospeech.TextToSpeechClient | None:
        cred_path = self.settings.google_application_credentials
        if cred_path and os.path.exists(cred_path):
            os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = os.path.abspath(cred_path)
            try:
                return texttospeech.TextToSpeechClient()
            except Exception as e:
                logger.warning("Could not initialize TextToSpeechClient: %s", e)
        return None

    def _get_stt_client(self) -> speech.SpeechClient | None:
        cred_path = self.settings.google_application_credentials
        if cred_path and os.path.exists(cred_path):
            os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = os.path.abspath(cred_path)
            try:
                return speech.SpeechClient()
            except Exception as e:
                logger.warning("Could not initialize SpeechClient: %s", e)
        return None

    async def synthesize_speech(
        self,
        text: str,
        voice_name: str = "en-US-Journey-F",
        language_code: str = "en-US",
        speaking_rate: float = 1.0,
        pitch: float = 0.0,
    ) -> bytes | None:
        """Synthesize text into MP3 audio bytes using Google Cloud TTS."""
        client = self._get_tts_client()
        if not client:
            return None

        def _sync_tts() -> bytes | None:
            try:
                s_input = texttospeech.SynthesisInput(text=text)
                voice = texttospeech.VoiceSelectionParams(
                    language_code=language_code,
                    name=voice_name,
                )
                audio_config = texttospeech.AudioConfig(
                    audio_encoding=texttospeech.AudioEncoding.MP3,
                    speaking_rate=speaking_rate,
                    pitch=pitch,
                )
                response = client.synthesize_speech(
                    input=s_input,
                    voice=voice,
                    audio_config=audio_config,
                )
                return response.audio_content
            except Exception as e:
                logger.warning("Google Cloud TTS failed (%s). Client will use Web Speech API.", e)
                return None

        return await asyncio.to_thread(_sync_tts)

    async def transcribe_audio(
        self,
        audio_bytes: bytes,
        sample_rate_hertz: int = 48000,
        language_code: str = "en-US",
    ) -> str | None:
        """Transcribe audio bytes using Google Cloud STT."""
        client = self._get_stt_client()
        if not client:
            return None

        def _sync_stt() -> str | None:
            try:
                audio = speech.RecognitionAudio(content=audio_bytes)
                config = speech.RecognitionConfig(
                    encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
                    sample_rate_hertz=sample_rate_hertz,
                    language_code=language_code,
                )
                response = client.recognize(config=config, audio=audio)
                transcripts = [res.alternatives[0].transcript for res in response.results if res.alternatives]
                return " ".join(transcripts) if transcripts else None
            except Exception as e:
                logger.warning("Google Cloud STT failed (%s). Client will use Web Speech API.", e)
                return None

        return await asyncio.to_thread(_sync_stt)


voice_service = VoiceService()
