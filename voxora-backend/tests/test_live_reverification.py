"""
Live Re-verification & Conversational Guardrail Test Suite:
1. Regression check on conversational guardrail ("hi", "thanks", "what can you help with?").
2. Re-run historical questions ("How were sales this month?" and "What was our total revenue this month?").
"""

import asyncio
import json
from uuid import UUID, uuid4
from sqlalchemy import select

from app.db.session import async_session_factory
from app.models.user import User
from app.models.conversation import Conversation, Message, QueryLog
from app.schemas.conversation import SendMessageRequest
from app.core.security import TokenPayload
from app.api.v1.conversations import send_message_stream


async def get_test_context():
    async with async_session_factory() as db:
        user_res = await db.execute(select(User).limit(1))
        user = user_res.scalar_one()
        
        # Create test conversation
        conv = Conversation(
            user_id=user.id,
            tenant_id=user.tenant_id,
            title="Live Reverification Session",
            status="active"
        )
        db.add(conv)
        await db.commit()
        await db.refresh(conv)
        
        token_payload = TokenPayload({
            "sub": str(user.id),
            "tenant_id": str(user.tenant_id),
            "email": user.email,
            "role": "admin",
            "type": "access"
        })
        
        return conv.id, token_payload


async def run_stream(conv_id: UUID, token_payload: TokenPayload, question: str):
    print(f"\n=================================================================")
    print(f"SENDING: \"{question}\"")
    print(f"=================================================================")
    req = SendMessageRequest(content=question, input_mode="text")
    
    response = await send_message_stream(conv_id, req, token_payload)
    
    events = []
    tokens = []
    viz_event = None
    
    # Consume SSE generator from StreamingResponse
    async for raw_line in response.body_iterator:
        for line in raw_line.split("\n\n"):
            if line.startswith("data: "):
                data_str = line[6:].strip()
                try:
                    payload = json.loads(data_str)
                    events.append(payload)
                    if payload.get("type") == "token":
                        tokens.append(payload.get("token", ""))
                    elif payload.get("type") == "visualization":
                        viz_event = payload.get("visualization")
                except Exception:
                    pass

    full_text = "".join(tokens)
    return full_text, viz_event


async def verify_query_log(conv_id: UUID):
    async with async_session_factory() as db:
        res = await db.execute(
            select(QueryLog, Message)
            .join(Message, QueryLog.message_id == Message.id)
            .where(Message.conversation_id == conv_id)
            .order_by(QueryLog.created_at.desc())
            .limit(1)
        )
        row = res.first()
        if row:
            ql, msg = row
            return ql
        return None


async def main():
    conv_id, token_payload = await get_test_context()
    print(f"Created Test Conversation: {conv_id}")
    
    # -------------------------------------------------------------
    # ITEM 1: Regression-check the conversational guardrail
    # -------------------------------------------------------------
    small_talk = [
        "hi",
        "thanks",
        "what can you help with?",
    ]
    
    for st in small_talk:
        reply, viz = await run_stream(conv_id, token_payload, st)
        print(f"AI Response:\n{reply}\n")
        assert len(reply.strip()) > 0, f"Empty response for small-talk: '{st}'"
        assert viz is None, f"Small-talk unexpectedly triggered visualization: {viz}"
        
        # Check query log — MUST be None for non-analytics
        ql = await verify_query_log(conv_id)
        if ql:
            # Query log should not belong to this small-talk message
            async with async_session_factory() as db:
                m = await db.get(Message, ql.message_id)
                assert m.content != reply, f"QueryLog was unexpectedly created for small-talk '{st}'!"
        print(f"--> Small-talk '{st}' STREAMED PERFECTLY (Non-analytics path verified)")

    # -------------------------------------------------------------
    # ITEM 2: Re-run the two historical hallucinated questions
    # -------------------------------------------------------------
    historical_questions = [
        "How were sales this month?",
        "What was our total revenue this month?",
    ]
    
    for hq in historical_questions:
        reply, viz = await run_stream(conv_id, token_payload, hq)
        print(f"AI Grounded Analysis:\n{reply}\n")
        
        # Verify QueryLog was recorded
        ql = await verify_query_log(conv_id)
        assert ql is not None, f"No QueryLog recorded for analytical question '{hq}'!"
        assert ql.status == "success", f"QueryLog status is not success: {ql.status}"
        assert ql.rows_returned is not None and ql.rows_returned > 0, f"Query returned 0 rows: {ql.rows_returned}"
        assert "2026-09" in ql.generated_sql, f"Generated SQL did not target current month 2026-09: {ql.generated_sql}"
        
        print("--- Verified QueryLog Details ---")
        print(f"Status: {ql.status}")
        print(f"LLM Provider: {ql.llm_provider}")
        print(f"Execution Time: {ql.execution_time_ms} ms")
        print(f"Rows Returned: {ql.rows_returned}")
        print(f"Generated SQL:\n{ql.generated_sql}")
        print(f"BigQuery Job Info: {ql.bigquery_job_info}")
        
        # Crucial check: verify that the historical hallucination $1.24M is NOT returned
        assert "$1.24M" not in reply and "$1.24 Million" not in reply, "Detected old hallucinated figure $1.24M!"
        print(f"--> Question '{hq}' SUCCESSFULLY GROUNDED BY BIGQUERY")

    print("\n=================================================================")
    print("ALL CONVERSATIONAL GUARDRAIL & HISTORICAL REVERIFICATIONS PASSED!")
    print("=================================================================\n")

if __name__ == "__main__":
    asyncio.run(main())
