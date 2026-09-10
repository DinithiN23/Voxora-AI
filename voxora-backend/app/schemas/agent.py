"""
Voxora Backend — Agent Studio Pydantic Schemas.

Request and response models for agent configuration, presets, test sandbox, and voice previews.
"""

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class GlossaryItem(BaseModel):
    """Business glossary definition."""

    term: str = Field(..., description="Business metric or terminology name")
    definition: str = Field(..., description="Plain-English formula, business rule, or definition")


class AgentConfigBase(BaseModel):
    """Base fields for agent configuration."""

    name: str = Field("Voxora Executive Copilot", max_length=100)
    avatar: str = Field("🤖", max_length=50)
    role_title: str = Field("Chief Analytics Officer", max_length=100)
    description: str = Field("Strategic C-suite intelligence advisor synthesizing metrics into decisive executive briefings.")
    tone: str = Field("executive", description="executive, analytical, strategic, technical")
    temperature: float = Field(0.2, ge=0.0, le=1.0)
    system_prompt: str
    greeting_message: str
    fallback_message: str
    voice_id: str = Field("en-US-Journey-F")
    voice_speed: float = Field(1.0, ge=0.5, le=2.0)
    voice_pitch: float = Field(0.0, ge=-20.0, le=20.0)
    allowed_data_areas: list[str] = Field(default_factory=lambda: ["Revenue & Finance", "Product Performance", "Customer Intelligence", "Regional Operations"])
    data_access_rules: dict[str, Any] = Field(default_factory=lambda: {"mask_pii": True, "read_only": True, "auto_visualize": True, "allow_sql_generation": True})
    knowledge_glossary: list[GlossaryItem] = Field(default_factory=list)
    is_active: bool = True


class AgentConfigUpdate(BaseModel):
    """Fields that can be updated in agent configuration."""

    name: str | None = None
    avatar: str | None = None
    role_title: str | None = None
    description: str | None = None
    tone: str | None = None
    temperature: float | None = Field(None, ge=0.0, le=1.0)
    system_prompt: str | None = None
    greeting_message: str | None = None
    fallback_message: str | None = None
    voice_id: str | None = None
    voice_speed: float | None = Field(None, ge=0.5, le=2.0)
    voice_pitch: float | None = Field(None, ge=-20.0, le=20.0)
    allowed_data_areas: list[str] | None = None
    data_access_rules: dict[str, Any] | None = None
    knowledge_glossary: list[GlossaryItem] | None = None
    is_active: bool | None = None


class AgentConfigResponse(AgentConfigBase):
    """Full agent configuration response with identifiers."""

    id: UUID
    tenant_id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class AgentPreset(BaseModel):
    """Pre-built agent persona template."""

    id: str
    name: str
    avatar: str
    role_title: str
    description: str
    tone: str
    temperature: float
    system_prompt: str
    greeting_message: str
    fallback_message: str
    voice_id: str
    voice_speed: float
    voice_pitch: float
    allowed_data_areas: list[str]
    data_access_rules: dict[str, Any]
    knowledge_glossary: list[GlossaryItem]


class AgentTestRequest(BaseModel):
    """Request to test agent prompt/tone in the sandbox."""

    question: str = Field(..., min_length=1, max_length=2000)
    system_prompt: str | None = None
    tone: str | None = None
    temperature: float | None = Field(None, ge=0.0, le=1.0)
    knowledge_glossary: list[GlossaryItem] | None = None


class AgentTestResponse(BaseModel):
    """Response from sandbox test bench."""

    response: str
    persona_applied: str
    tone_applied: str
    model_used: str
    latency_ms: int


class VoicePreviewRequest(BaseModel):
    """Request to generate voice sample preview."""

    text: str = Field(..., max_length=500)
    voice_id: str = Field("en-US-Journey-F")
    speed: float = Field(1.0, ge=0.5, le=2.0)
    pitch: float = Field(0.0, ge=-20.0, le=20.0)
