"""
Voxora Backend — AI Business Analyst Service.

Interprets BigQuery execution results and synthesizes executive-level analysis,
highlighting key drivers, metrics, and actionable takeaways.
"""

from collections.abc import AsyncGenerator
import json
import logging
from typing import Any

from app.services.llm_service import llm_service

logger = logging.getLogger(__name__)

ANALYST_SYSTEM_PROMPT = """You are Voxora AI, an executive Chief Analytics Officer and Business Intelligence Copilot.
You are given the user's question, the BigQuery SQL query executed, and the exact query results.

Your task is to write a crisp, professional, C-suite executive briefing:
1. Lead directly with the single most important number or key finding in bold.
2. Provide concise bullet points detailing key comparisons, top drivers, or percentages.
3. If applicable, add a 1-sentence strategic takeaway or recommendation.
4. Keep the tone sharp, authoritative, and data-backed. Never mention SQL technical details unless explicitly asked.
"""


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

        active_prompt = system_prompt or ANALYST_SYSTEM_PROMPT
        async for chunk in llm_service.stream_response(messages, system_prompt=active_prompt):
            yield chunk


ai_analyst_service = AIAnalystService()
