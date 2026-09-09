"""
Voxora Backend — Voice API Endpoints.

Handles server-side Speech-to-Text and Text-to-Speech requests.
"""

from fastapi import APIRouter, HTTPException, UploadFile, File, Response, status
from pydantic import BaseModel
from app.services.voice_service import voice_service

router = APIRouter(prefix="/voice", tags=["Voice"])


class SynthesizeRequest(BaseModel):
    text: str
    voice_name: str = "en-US-Journey-F"
    language_code: str = "en-US"


class TranscribeResponse(BaseModel):
    transcript: str


@router.post("/synthesize")
async def synthesize_speech(request: SynthesizeRequest):
    """Synthesize text into speech audio bytes."""
    if not request.text.strip():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Text cannot be empty")

    audio_bytes = await voice_service.synthesize_speech(
        text=request.text,
        voice_name=request.voice_name,
        language_code=request.language_code,
    )

    if not audio_bytes:
        # Client can fall back to browser Web Speech API
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Cloud TTS unavailable, fallback to browser Web Speech API.",
        )

    return Response(content=audio_bytes, media_type="audio/mpeg")


@router.post("/transcribe", response_model=TranscribeResponse)
async def transcribe_audio(file: UploadFile = File(...)):
    """Transcribe uploaded audio file to text."""
    audio_content = await file.read()
    transcript = await voice_service.transcribe_audio(audio_content)

    if not transcript:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Could not transcribe audio.",
        )

    return TranscribeResponse(transcript=transcript)


@router.get("/voices")
async def list_recommended_voices():
    """List recommended natural voice presets."""
    return [
        {"id": "en-US-Journey-F", "name": "Voxora Natural Female (Journey)", "gender": "Female", "provider": "Google"},
        {"id": "en-US-Journey-D", "name": "Voxora Natural Male (Journey)", "gender": "Male", "provider": "Google"},
        {"id": "en-US-Neural2-F", "name": "Executive Studio Female", "gender": "Female", "provider": "Google"},
        {"id": "en-US-Neural2-D", "name": "Executive Studio Male", "gender": "Male", "provider": "Google"},
    ]
