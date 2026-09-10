"""
Voxora Backend — Agent Studio API Endpoints.

Provides administrative controls for configuring Voxora's persona, tone,
system prompt, voice settings, glossary, and sandbox testing.
"""

import logging
from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import TokenPayload, get_current_user
from app.db.session import get_db
from app.schemas.agent import (
    AgentConfigResponse,
    AgentConfigUpdate,
    AgentPreset,
    AgentTestRequest,
    AgentTestResponse,
    VoicePreviewRequest,
)
from app.services.agent_service import agent_studio_service
from app.services.voice_service import VoiceService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/studio", tags=["Agent Studio"])
voice_service = VoiceService()


@router.get("/agent", response_model=AgentConfigResponse)
async def get_agent_config(
    current_user: TokenPayload = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Retrieve the current tenant's active agent configuration."""
    config = await agent_studio_service.get_or_create_config(current_user.tenant_id, db)
    return config


@router.put("/agent", response_model=AgentConfigResponse)
async def update_agent_config(
    update_data: AgentConfigUpdate,
    current_user: TokenPayload = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update persona, tone, prompts, voice, or knowledge glossary for the tenant."""
    config = await agent_studio_service.update_config(
        tenant_id=current_user.tenant_id,
        update_data=update_data,
        db=db,
    )
    return config


@router.post("/agent/reset", response_model=AgentConfigResponse)
async def reset_agent_config(
    current_user: TokenPayload = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Reset the tenant's agent configuration to the standard factory default."""
    config = await agent_studio_service.reset_config(current_user.tenant_id, db)
    return config


@router.get("/presets", response_model=list[AgentPreset])
async def list_presets(
    current_user: TokenPayload = Depends(get_current_user),
):
    """List available pre-configured agent persona templates."""
    return agent_studio_service.get_presets()


@router.post("/test", response_model=AgentTestResponse)
async def test_agent_sandbox(
    request: AgentTestRequest,
    current_user: TokenPayload = Depends(get_current_user),
):
    """Test custom prompt, tone, and glossary rules in an isolated sandbox environment."""
    return await agent_studio_service.run_test_bench(request)


@router.post("/voice-preview")
async def preview_voice(
    request: VoicePreviewRequest,
    current_user: TokenPayload = Depends(get_current_user),
):
    """Generate an audio preview of the configured voice, speaking rate, and pitch."""
    audio_bytes = await voice_service.synthesize_speech(
        text=request.text,
        voice_name=request.voice_id,
        speaking_rate=request.speed,
        pitch=request.pitch,
    )

    if not audio_bytes:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Cloud TTS unavailable. Using client-side Web Speech preview.",
        )

    return Response(content=audio_bytes, media_type="audio/mpeg")
