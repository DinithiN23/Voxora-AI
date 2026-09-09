"""
Voxora Backend — Conversation schemas.

Request/response schemas for conversation and message endpoints.
"""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


# ── Visualization ────────────────────────────────────────────

class VisualizationResponse(BaseModel):
    """A chart/visualization attached to a message."""
    id: UUID
    chart_type: str
    chart_config: dict
    data_payload: dict
    title: str | None = None

    model_config = {"from_attributes": True}


# ── Messages ─────────────────────────────────────────────────

class SendMessageRequest(BaseModel):
    """User sends a message (question) to Voxora."""
    content: str = Field(min_length=1, max_length=2000)
    input_mode: str = Field(default="text", pattern="^(text|voice)$")


class MessageResponse(BaseModel):
    """A single message in a conversation."""
    id: UUID
    role: str
    content: str
    input_mode: str
    intent: dict | None = None
    entities: dict | None = None
    visualizations: list[VisualizationResponse] = []
    created_at: datetime

    model_config = {"from_attributes": True}


# ── Conversations ────────────────────────────────────────────

class CreateConversationRequest(BaseModel):
    """Start a new conversation."""
    title: str | None = None


class ConversationResponse(BaseModel):
    """A conversation summary."""
    id: UUID
    title: str | None = None
    status: str
    message_count: int = 0
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ConversationDetailResponse(BaseModel):
    """A conversation with all messages."""
    id: UUID
    title: str | None = None
    status: str
    messages: list[MessageResponse] = []
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# ── AI Response ──────────────────────────────────────────────

class AskResponse(BaseModel):
    """Full response from Voxora after processing a question."""
    message: MessageResponse
    suggestions: list[str] = []
    voice_url: str | None = None
