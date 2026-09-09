"""
Voxora Backend — Conversations API endpoints.

Handles conversation CRUD and message sending (the core "Ask Voxora" flow).
"""

import json
import logging
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import TokenPayload, get_current_user
from app.db.session import async_session_factory, get_db
from app.models.conversation import Conversation, Message
from app.schemas.conversation import (
    AskResponse,
    ConversationDetailResponse,
    ConversationResponse,
    CreateConversationRequest,
    MessageResponse,
    SendMessageRequest,
    UpdateConversationRequest,
    VisualizationResponse,
)
from app.services.llm_service import llm_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/conversations", tags=["Conversations"])


@router.post("", response_model=ConversationResponse, status_code=status.HTTP_201_CREATED)
async def create_conversation(
    request: CreateConversationRequest,
    current_user: TokenPayload = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Start a new conversation."""

    conversation = Conversation(
        user_id=current_user.user_id,
        tenant_id=current_user.tenant_id,
        title=request.title,
        context_stack={},
    )
    db.add(conversation)
    await db.flush()

    return ConversationResponse(
        id=conversation.id,
        title=conversation.title,
        status=conversation.status,
        message_count=0,
        created_at=conversation.created_at,
        updated_at=conversation.updated_at,
    )


@router.get("", response_model=list[ConversationResponse])
async def list_conversations(
    current_user: TokenPayload = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    limit: int = 50,
    offset: int = 0,
):
    """List the current user's conversations."""

    # Get conversations with message count
    query = (
        select(
            Conversation,
            func.count(Message.id).label("message_count"),
        )
        .outerjoin(Message, Message.conversation_id == Conversation.id)
        .where(
            Conversation.user_id == current_user.user_id,
            Conversation.tenant_id == current_user.tenant_id,
            Conversation.status == "active",
        )
        .group_by(Conversation.id)
        .order_by(Conversation.updated_at.desc())
        .limit(limit)
        .offset(offset)
    )

    result = await db.execute(query)
    rows = result.all()

    return [
        ConversationResponse(
            id=conv.id,
            title=conv.title,
            status=conv.status,
            message_count=count,
            created_at=conv.created_at,
            updated_at=conv.updated_at,
        )
        for conv, count in rows
    ]


@router.get("/{conversation_id}", response_model=ConversationDetailResponse)
async def get_conversation(
    conversation_id: UUID,
    current_user: TokenPayload = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get a conversation with all its messages."""

    result = await db.execute(
        select(Conversation).where(
            Conversation.id == conversation_id,
            Conversation.user_id == current_user.user_id,
        )
    )
    conversation = result.scalar_one_or_none()

    if not conversation:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found")

    messages = [
        MessageResponse(
            id=msg.id,
            role=msg.role,
            content=msg.content,
            input_mode=msg.input_mode,
            intent=msg.intent,
            entities=msg.entities,
            visualizations=[
                VisualizationResponse(
                    id=viz.id,
                    chart_type=viz.chart_type,
                    chart_config=viz.chart_config,
                    data_payload=viz.data_payload,
                    title=viz.title,
                )
                for viz in msg.visualizations
            ],
            created_at=msg.created_at,
        )
        for msg in conversation.messages
    ]

    return ConversationDetailResponse(
        id=conversation.id,
        title=conversation.title,
        status=conversation.status,
        messages=messages,
        created_at=conversation.created_at,
        updated_at=conversation.updated_at,
    )


@router.post("/{conversation_id}/messages", response_model=AskResponse)
async def send_message(
    conversation_id: UUID,
    request: SendMessageRequest,
    current_user: TokenPayload = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Send a message to a conversation — this is the core 'Ask Voxora' endpoint.

    For Phase 1, this returns a basic AI response without data queries.
    Phase 2 will add intent detection, BigQuery, and visualizations.
    """

    # Verify conversation belongs to user
    result = await db.execute(
        select(Conversation).where(
            Conversation.id == conversation_id,
            Conversation.user_id == current_user.user_id,
        )
    )
    conversation = result.scalar_one_or_none()

    if not conversation:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found")

    # Save user message
    user_message = Message(
        conversation_id=conversation.id,
        role="user",
        content=request.content,
        input_mode=request.input_mode,
    )
    db.add(user_message)
    await db.flush()

    # Build conversational history for context
    history_result = await db.execute(
        select(Message)
        .where(Message.conversation_id == conversation.id)
        .order_by(Message.created_at.asc())
    )
    history_messages = history_result.scalars().all()

    chat_history = [
        {"role": m.role, "content": m.content}
        for m in history_messages
        if m.role in ("user", "assistant")
    ]

    # Auto-generate title if this is the first interaction
    if not conversation.title or conversation.title == "New Conversation":
        conversation.title = request.content[:60]

    # Call AI Engine (Gemini with Groq fallback)
    try:
        ai_response_text = await llm_service.generate_response(chat_history)
    except Exception:
        ai_response_text = _generate_placeholder_response(request.content)

    ai_message = Message(
        conversation_id=conversation.id,
        role="assistant",
        content=ai_response_text,
        input_mode="text",
    )
    db.add(ai_message)
    await db.flush()

    # Build response
    response_message = MessageResponse(
        id=ai_message.id,
        role=ai_message.role,
        content=ai_message.content,
        input_mode=ai_message.input_mode,
        intent=ai_message.intent,
        entities=ai_message.entities,
        visualizations=[],
        created_at=ai_message.created_at,
    )

    suggestions = await llm_service.generate_suggestions(request.content, ai_response_text)

    return AskResponse(
        message=response_message,
        suggestions=suggestions,
        voice_url=None,
    )


@router.post("/{conversation_id}/messages/stream")
async def send_message_stream(
    conversation_id: UUID,
    request: SendMessageRequest,
    current_user: TokenPayload = Depends(get_current_user),
):
    """
    Stream AI responses using Server-Sent Events (SSE).

    Flow:
    1. Validates and saves the user question to PostgreSQL.
    2. Auto-generates conversation title if it's the first message.
    3. Streams LLM tokens in real time (via Groq / fallback).
    4. Persists the complete assistant response into PostgreSQL.
    5. Yields final metadata event with follow-up suggestion chips.
    """

    async def event_generator():
        async with async_session_factory() as db:
            try:
                # 1. Verify conversation belongs to user
                result = await db.execute(
                    select(Conversation).where(
                        Conversation.id == conversation_id,
                        Conversation.user_id == current_user.user_id,
                    )
                )
                conversation = result.scalar_one_or_none()
                if not conversation:
                    yield f"data: {json.dumps({'type': 'error', 'error': 'Conversation not found'})}\n\n"
                    return

                # 2. Save user message
                user_msg = Message(
                    conversation_id=conversation.id,
                    role="user",
                    content=request.content,
                    input_mode=request.input_mode,
                )
                db.add(user_msg)

                # Auto-title if new or empty
                if not conversation.title or conversation.title == "New Conversation":
                    conversation.title = request.content[:60]

                await db.commit()

                # 3. Fetch chat history for conversational context
                history_result = await db.execute(
                    select(Message)
                    .where(Message.conversation_id == conversation.id)
                    .order_by(Message.created_at.asc())
                )
                chat_history = [
                    {"role": m.role, "content": m.content}
                    for m in history_result.scalars().all()
                    if m.role in ("user", "assistant")
                ]

                # 4. Stream LLM tokens
                collected_chunks: list[str] = []
                try:
                    async for chunk in llm_service.stream_response(chat_history):
                        collected_chunks.append(chunk)
                        yield f"data: {json.dumps({'type': 'token', 'token': chunk})}\n\n"
                except Exception as stream_err:
                    logger.error("Streaming error: %s", stream_err)
                    fallback_chunk = _generate_placeholder_response(request.content)
                    collected_chunks.append(fallback_chunk)
                    yield f"data: {json.dumps({'type': 'token', 'token': fallback_chunk})}\n\n"

                full_content = "".join(collected_chunks).strip()

                # 5. Persist assistant message to DB
                ai_msg = Message(
                    conversation_id=conversation.id,
                    role="assistant",
                    content=full_content,
                    input_mode="text",
                )
                db.add(ai_msg)
                await db.commit()
                await db.refresh(ai_msg)

                # 6. Generate smart follow-up suggestions
                suggestions = await llm_service.generate_suggestions(request.content, full_content)

                # 7. Yield final completion event
                yield f"data: {json.dumps({'type': 'done', 'message_id': str(ai_msg.id), 'suggestions': suggestions, 'title': conversation.title})}\n\n"

            except Exception as e:
                logger.error("Fatal error in stream generator: %s", e)
                yield f"data: {json.dumps({'type': 'error', 'error': str(e)})}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.patch("/{conversation_id}", response_model=ConversationResponse)
async def update_conversation(
    conversation_id: UUID,
    request: UpdateConversationRequest,
    current_user: TokenPayload = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update conversation title or archive status."""

    result = await db.execute(
        select(Conversation).where(
            Conversation.id == conversation_id,
            Conversation.user_id == current_user.user_id,
        )
    )
    conversation = result.scalar_one_or_none()

    if not conversation:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found")

    if request.title is not None:
        conversation.title = request.title.strip()
    if request.status is not None:
        conversation.status = request.status

    await db.flush()

    count_res = await db.execute(
        select(func.count(Message.id)).where(Message.conversation_id == conversation.id)
    )
    message_count = count_res.scalar() or 0

    return ConversationResponse(
        id=conversation.id,
        title=conversation.title,
        status=conversation.status,
        message_count=message_count,
        created_at=conversation.created_at,
        updated_at=conversation.updated_at,
    )


@router.delete("/{conversation_id}", status_code=status.HTTP_204_NO_CONTENT)
async def archive_conversation(
    conversation_id: UUID,
    current_user: TokenPayload = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Archive (soft-delete) a conversation."""

    result = await db.execute(
        select(Conversation).where(
            Conversation.id == conversation_id,
            Conversation.user_id == current_user.user_id,
        )
    )
    conversation = result.scalar_one_or_none()

    if not conversation:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found")

    conversation.status = "archived"
    await db.flush()


def _generate_placeholder_response(question: str) -> str:
    """Phase 1 placeholder — returns a contextual demo response.

    Will be replaced by the full AI pipeline in Phase 2.
    """
    q = question.lower()

    if "sales" in q and ("month" in q or "today" in q):
        return (
            "Based on the available data, September sales are currently tracking at **$2.4M**, "
            "which represents an **8.7% increase** compared to the same period last month.\n\n"
            "Key highlights:\n"
            "- Daily average: $343K\n"
            "- Strongest day: September 3 ($412K)\n"
            "- On track to exceed the monthly target of $3.2M"
        )
    elif "top" in q and "product" in q:
        return (
            "Here are the **top-selling products** this month:\n\n"
            "| Rank | Product | Units | Revenue |\n"
            "|------|---------|-------|---------|\n"
            "| 1 | Product A | 12,450 | $430K |\n"
            "| 2 | Product B | 10,320 | $381K |\n"
            "| 3 | Product C | 8,940 | $312K |\n"
            "| 4 | Product D | 6,780 | $242K |\n"
            "| 5 | Product E | 5,210 | $194K |\n\n"
            "**Product A** is the clear leader, contributing approximately **18%** of total product revenue. "
            "Product B is close behind with strong growth in the Eastern region."
        )
    elif "compare" in q or "last month" in q:
        return (
            "Comparing current month with last month:\n\n"
            "| Metric | This Month | Last Month | Change |\n"
            "|--------|-----------|------------|--------|\n"
            "| Revenue | $2.4M | $2.21M | ↑ 8.7% |\n"
            "| Orders | 3,842 | 3,510 | ↑ 9.5% |\n"
            "| Avg Order Value | $625 | $630 | ↓ 0.8% |\n"
            "| New Customers | 284 | 251 | ↑ 13.1% |\n\n"
            "Revenue is growing primarily due to **higher order volume** rather than increased order values. "
            "The 13.1% increase in new customers is a particularly positive signal."
        )
    elif "why" in q and ("drop" in q or "decrease" in q or "fell" in q or "decline" in q):
        return (
            "Analysing the performance decline:\n\n"
            "The largest contributing factor was a **22% decrease in order volume from the Western region**.\n\n"
            "Potential causes:\n"
            "- A major distributor in the Western region reported inventory issues\n"
            "- Competitor launched a promotional campaign in the same region\n"
            "- Seasonal patterns show historical softness in this period\n\n"
            "Would you like me to drill deeper into the Western region data?"
        )
    else:
        return (
            "I understand your question. In the current preview, I'm using sample responses "
            "to demonstrate the conversational flow.\n\n"
            "Once connected to your data sources, I'll be able to:\n"
            "- Query your business data in real-time\n"
            "- Provide accurate insights and analysis\n"
            "- Generate dynamic visualizations\n"
            "- Remember context for follow-up questions\n\n"
            "Try asking about **sales performance**, **top products**, or **comparisons**!"
        )


def _generate_suggestions(question: str) -> list[str]:
    """Generate follow-up question suggestions based on the current question."""
    q = question.lower()

    if "sales" in q:
        return [
            "What are the top-performing products?",
            "Compare with last month",
            "Show sales by region",
            "Which region is growing fastest?",
        ]
    elif "product" in q:
        return [
            "Compare these with last month",
            "Show revenue by region for Product A",
            "Which products are declining?",
            "What's the profit margin by product?",
        ]
    elif "compare" in q:
        return [
            "Why did revenue increase?",
            "Show the trend over 6 months",
            "Which category grew the most?",
            "Forecast next month",
        ]
    else:
        return [
            "How are sales this month?",
            "Show top-selling products",
            "Compare this month with last month",
            "What are the key trends?",
        ]
