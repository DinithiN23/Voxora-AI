"""
Voxora Backend — AI Business Analyst Service.

Interprets BigQuery execution results and synthesizes executive-level analysis,
highlighting key drivers, metrics, and actionable takeaways.
"""

from collections.abc import AsyncGenerator
from datetime import date, timedelta
import json
import logging
from typing import Any

from app.services.llm_service import llm_service

logger = logging.getLogger(__name__)


def get_analyst_system_prompt(custom_persona_prompt: str | None = None) -> str:
    today = date.today()
    yesterday = today - timedelta(days=1)
    today_str = today.strftime("%B %d, %Y")
    yesterday_str = yesterday.strftime("%B %d, %Y")
    current_month = today.strftime("%B %Y")

    # 1 month ago
    m1_year = today.year if today.month > 1 else today.year - 1
    m1_month = today.month - 1 if today.month > 1 else 12
    last_month = date(m1_year, m1_month, 1).strftime("%B %Y")

    # 3 months ago
    m3_month = ((today.month - 1 - 3) % 12) + 1
    m3_year = today.year if today.month > 3 else today.year - 1
    m3_name = date(m3_year, m3_month, 1).strftime("%B %Y")

    base_rules = f"""You are Voxora AI, an executive Chief Analytics Officer and Business Intelligence Copilot.
You are given the user's question, the BigQuery SQL query executed, and the exact query results.

Executive Briefing Principles:
1. Lead directly with the single most critical figure in bold (e.g. "**Today's sales revenue (September 12, 2026) is $23,650.00**").
2. Temporal Accuracy (GROUND TRUTH):
   - Today's date: {today_str}.
   - Yesterday's date: {yesterday_str}.
   - Current active month: {current_month}.
   - Last completed month: {last_month}.
   - Multi-month windows (e.g. "from this month to last 3 months"): {m3_name} through {today_str}.
   - When the user asks about "today", ALWAYS explicitly state {today_str}. Never confuse it with past seed dates.
   - When the user asks for multi-month totals, state both the aggregate total and key monthly drivers.
3. Provide concise bullet points detailing key metrics (order counts, profit margin %, AOV).
4. If applicable, add a 1-sentence strategic takeaway or operational observation.
5. Keep the tone sharp, authoritative, and data-backed. Never expose raw SQL errors, query syntax, or database mechanics unless requested.
"""
    if custom_persona_prompt:
        return f"{custom_persona_prompt}\n\n{base_rules}"
    return base_rules


class AIAnalystService:
    """Generates executive commentary from query results."""

    async def stream_analysis(
        self,
        question: str,
        sql: str,
        query_result: dict[str, Any],
        chat_history: list[dict[str, str]] | None = None,
        system_prompt: str | None = None,
    ) -> AsyncGenerator[str, None]:
        """Stream executive analysis for a completed BigQuery query."""
        rows_sample = query_result.get("rows", [])[:20]
        row_count = query_result.get("row_count", 0)

        prompt = (
            f"User Question: '{question}'\n\n"
            f"Executed BigQuery SQL:\n{sql}\n\n"
            f"Query Results ({row_count} total rows):\n"
            f"{json.dumps(rows_sample, indent=2)}\n\n"
            "Synthesize this data into an executive briefing."
        )

        messages = [
            {"role": "user", "content": prompt}
        ]

        active_prompt = get_analyst_system_prompt(system_prompt)
        async for chunk in llm_service.stream_response(messages, system_prompt=active_prompt):
            yield chunk


ai_analyst_service = AIAnalystService()
