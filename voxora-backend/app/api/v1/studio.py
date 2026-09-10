"""
Voxora Backend — Agent Studio API Endpoints.

Provides administrative controls for configuring Voxora's persona, tone,
system prompt, voice settings, glossary, and sandbox testing.
"""

import logging
from datetime import UTC, datetime
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import TokenPayload, get_current_user, get_current_user_optional
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
    current_user: TokenPayload | None = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db),
):
    """Retrieve the current tenant's active agent configuration, or default preset if unauthenticated."""
    if current_user:
        config = await agent_studio_service.get_or_create_config(current_user.tenant_id, db)
        return config

    # Fallback to default preset in demo/guest mode
    default_preset = agent_studio_service.get_presets()[0]
    now = datetime.now(UTC)
    return AgentConfigResponse(
        id=UUID("00000000-0000-0000-0000-000000000000"),
        tenant_id=UUID("00000000-0000-0000-0000-000000000000"),
        name=default_preset.name,
        avatar=default_preset.avatar,
        role_title=default_preset.role_title,
        description=default_preset.description,
        tone=default_preset.tone,
        temperature=default_preset.temperature,
        system_prompt=default_preset.system_prompt,
        greeting_message=default_preset.greeting_message,
        fallback_message=default_preset.fallback_message,
        voice_id=default_preset.voice_id,
        voice_speed=default_preset.voice_speed,
        voice_pitch=default_preset.voice_pitch,
        allowed_data_areas=default_preset.allowed_data_areas,
        data_access_rules=default_preset.data_access_rules,
        knowledge_glossary=default_preset.knowledge_glossary,
        is_active=True,
        created_at=now,
        updated_at=now,
    )


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
async def list_presets():
    """List available pre-configured agent persona templates."""
    return agent_studio_service.get_presets()


@router.post("/test", response_model=AgentTestResponse)
async def test_agent_sandbox(
    request: AgentTestRequest,
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
