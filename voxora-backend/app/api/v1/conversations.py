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
from app.models.conversation import Conversation, Message, QueryLog, Visualization
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
from app.integrations.bigquery.client import bigquery_client
from app.services.agent_service import agent_studio_service
from app.services.ai_analyst import ai_analyst_service
from app.services.llm_service import llm_service
from app.services.text_to_sql import text_to_sql_engine
from app.services.visualization_service import visualization_service

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

    # Call AI Engine with tenant agent configuration
    try:
        agent_cfg = await agent_studio_service.get_or_create_config(current_user.tenant_id, db)
        effective_prompt = agent_studio_service.build_effective_system_prompt(agent_cfg)
        ai_response_text, provider = await llm_service.generate_response(chat_history, system_prompt=effective_prompt)
    except Exception:
        ai_response_text = "I encountered a connection error and could not complete your request. Please try again."

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

                # 4. Text-to-SQL & BigQuery Analytical Pipeline
                collected_chunks: list[str] = []
                active_viz_config: dict | None = None
                executed_sql: str | None = None
                query_res: dict | None = None

                # Detect if question is likely requesting business analytics
                is_analytics_query = any(k in request.content.lower() for k in (
                    "revenue", "sale", "order", "product", "customer", "region", "profit",
                    "margin", "top", "trend", "compare", "month", "breakdown", "performance",
                    "channel", "growth", "kpi", "metric", "cost", "average", "highest", "lowest"
                ))

                if is_analytics_query:
                    try:
                        sql_res = await text_to_sql_engine.generate_sql(
                            request.content, chat_history
                        )
                        executed_sql = sql_res.sql
                        provider = sql_res.provider
                        was_auto_scoped = getattr(sql_res, "was_auto_scoped", False)

                        # If query was auto-scoped to 30 days, notify the user visually
                        if was_auto_scoped:
                            notice = "> ℹ️ *No specific timeframe was provided — showing data from the last 30 days (UTC).*\n\n"
                            collected_chunks.append(notice)
                            yield f"data: {json.dumps({'type': 'token', 'token': notice})}\n\n"

                        query_res = await bigquery_client.execute_query(executed_sql)

                        # Check for recommended chart
                        active_viz_config = visualization_service.recommend_visualization(
                            request.content, executed_sql, query_res
                        )

                        # Emit visualization event before streaming text
                        if active_viz_config:
                            yield f"data: {json.dumps({'type': 'visualization', 'visualization': active_viz_config})}\n\n"

                        # Load tenant agent configuration for persona, tone, and glossary
                        try:
                            agent_cfg = await agent_studio_service.get_or_create_config(current_user.tenant_id, db)
                            effective_prompt = agent_studio_service.build_effective_system_prompt(agent_cfg)
                        except Exception:
                            effective_prompt = None

                        # Stream executive commentary based on real BigQuery data
                        async for chunk in ai_analyst_service.stream_analysis(
                            request.content, executed_sql, query_res, chat_history, system_prompt=effective_prompt
                        ):
                            collected_chunks.append(chunk)
                            yield f"data: {json.dumps({'type': 'token', 'token': chunk})}\n\n"

                    except Exception as bq_err:
                        logger.error("BigQuery analytics pipeline failure: %s", bq_err, exc_info=True)
                        active_viz_config = None
                        err_msg = (
                            "⚠️ **Data Retrieval Notice**: I was unable to retrieve the underlying business data from the warehouse "
                            f"to answer this question accurately (`{str(bq_err)}`).\n\n"
                            "To preserve data integrity, ungrounded estimates will not be displayed. Please refine your query or contact your system administrator."
                        )
                        collected_chunks.append(err_msg)
                        yield f"data: {json.dumps({'type': 'token', 'token': err_msg})}\n\n"

                # Fallback to direct conversational response ONLY if not an analytics query
                if not is_analytics_query and not collected_chunks:
                    try:
                        agent_cfg = await agent_studio_service.get_or_create_config(current_user.tenant_id, db)
                        effective_prompt = agent_studio_service.build_effective_system_prompt(agent_cfg)
                    except Exception:
                        effective_prompt = None

                    try:
                        async for chunk in llm_service.stream_response(chat_history, system_prompt=effective_prompt):
                            collected_chunks.append(chunk)
                            yield f"data: {json.dumps({'type': 'token', 'token': chunk})}\n\n"
                    except Exception as stream_err:
                        logger.error("Streaming error: %s", stream_err)
                        fallback_chunk = "I encountered a connection error and could not complete your request. Please try again."
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

                # Persist Visualization to DB if generated
                if active_viz_config:
                    try:
                        viz_record = Visualization(
                            message_id=ai_msg.id,
                            chart_type=active_viz_config.get("chart_type", "bar"),
                            title=active_viz_config.get("title"),
                            chart_config=active_viz_config.get("chart_config", {}),
                            data_payload=active_viz_config.get("data_payload", {}),
                        )
                        db.add(viz_record)
                        await db.commit()
                    except Exception as viz_err:
                        logger.error("Failed to persist visualization: %s", viz_err)

                # Persist QueryLog to DB if SQL executed or attempted
                if executed_sql:
                    try:
                        bytes_billed = query_res.get("bytes_billed", 0) if query_res else 0
                        status_str = "success" if query_res else "error"
                        logger.info(
                            "QueryLog: recorded BigQuery SQL status=%s, job_id=%s, execution_time_ms=%s, bytes_billed=%s (%.2f MB), provider=%s",
                            status_str,
                            query_res.get("job_id") if query_res else None,
                            query_res.get("execution_time_ms") if query_res else None,
                            bytes_billed,
                            bytes_billed / (1024 * 1024) if bytes_billed else 0.0,
                            provider
                        )

                        query_log = QueryLog(
                            message_id=ai_msg.id,
                            generated_sql=executed_sql,
                            execution_time_ms=query_res.get("execution_time_ms") if query_res else None,
                            rows_returned=query_res.get("row_count") if query_res else None,
                            status=status_str,
                            llm_provider=provider,
                            bigquery_job_info={
                                "job_id": query_res.get("job_id") if query_res else None,
                                "bytes_billed": bytes_billed,
                                "llm_provider": provider,
                                "error": str(bq_err) if 'bq_err' in locals() and bq_err else None,
                            },
                        )
                        db.add(query_log)
                        await db.commit()
                    except Exception as log_err:
                        logger.error("Failed to persist query log: %s", log_err)

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


@router.get("/{conversation_id}/summary")
async def get_conversation_summary(
    conversation_id: UUID,
    current_user: TokenPayload = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Generate a dynamic summary of the conversation so far.
    """
    result = await db.execute(
        select(Conversation).where(
            Conversation.id == conversation_id,
            Conversation.user_id == current_user.user_id,
        )
    )
    conversation = result.scalar_one_or_none()

    if not conversation:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found")

    history_result = await db.execute(
        select(Message)
        .where(Message.conversation_id == conversation.id)
        .order_by(Message.created_at.asc())
    )
    history_messages = history_result.scalars().all()

    if len(history_messages) < 2:
        return {"summary": "Not enough conversation history to summarize yet. Chat a bit more first!"}

    chat_history = [
        {"role": m.role, "content": m.content}
        for m in history_messages
        if m.role in ("user", "assistant")
    ]

    prompt = (
        "You are a business intelligence summarizer. Read the following conversation between a user and an AI analytics assistant. "
        "Provide a concise, bulleted executive summary of the key insights, metrics, and conclusions discussed in the chat. "
        "Keep it strictly under 150 words. Do not introduce new information."
    )

    try:
        summary_text, _ = await llm_service.generate_response(chat_history, system_prompt=prompt)
    except Exception:
        summary_text = "Summary unavailable due to connection issues."

    return {"summary": summary_text}


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
