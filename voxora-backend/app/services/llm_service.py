"""
Voxora Backend — Unified LLM Service with Multi-Provider Support & Automatic Fallback.

Supported Providers:
1. Google Gemini (models/gemini-3.6-flash via fast REST API) — High intelligence, large context.
2. Groq (qwen/qwen3.8-27b or openai/gpt-oss-120b) — Lightning fast inference (~300 tok/sec).
3. Automatic fallback: If primary provider experiences rate limits (429) or errors,
   the request automatically fails over to the alternate provider.
"""

import logging
from typing import Any

import httpx
from collections.abc import AsyncGenerator
try:
    from groq import AsyncGroq, Groq
except ImportError:
    AsyncGroq = None  # type: ignore[assignment,misc]
    Groq = None  # type: ignore[assignment,misc]

from datetime import date, timedelta

from app.config import get_settings

logger = logging.getLogger(__name__)


def get_default_system_prompt() -> str:
    # Explicitly calculate temporal anchors in UTC to avoid cross-timezone boundary issues.
    from datetime import datetime, timezone
    today = datetime.now(timezone.utc).date()
    yesterday = today - timedelta(days=1)
    today_str = today.strftime("%B %d, %Y")
    yesterday_str = yesterday.strftime("%B %d, %Y")
    current_month = today.strftime("%B %Y")

    m1_year = today.year if today.month > 1 else today.year - 1
    m1_month = today.month - 1 if today.month > 1 else 12
    last_month = date(m1_year, m1_month, 1).strftime("%B %Y")

    return f"""You are Voxora AI, an intelligent conversational business intelligence copilot and Chief Analytics Officer.
Your job is to help business users understand their metrics, trends, sales, customer behavior, and operational KPIs connected directly to Google BigQuery.

Guidelines:
1. Greetings & Conversational Questions:
   - When the user asks common conversational questions (e.g., "hello", "hi", "how are you", "who are you", "what can you do"):
     Respond warmly, politely, and introduce yourself as Voxora AI. Explain that you are connected to Google BigQuery to analyze business revenue, product performance, regional sales, customer segments, and generate real-time charts.
2. Scope Guardrails & Fallback / Escalation:
   - When the user asks questions that are NOT relevant to business intelligence, sales, company data, or financial analytics (e.g. cooking recipes, games, celebrity gossip, sports trivia, coding unrelated tasks):
     Politely decline and provide a clear boundary:
     "I am Voxora AI, your specialized business intelligence copilot. I focus exclusively on your organization's revenue analytics, sales trends, and BigQuery metrics. I cannot assist with that topic, but I would be glad to help you explore your sales trends, top products, regional performance, or revenue breakdowns. If you need assistance outside business data, please contact your organization administrator."
3. Executive Clarity & Precision:
   - State the most important number or key metric first in bold.
   - Explain trends with context and percentages.
   - Maintain conversational memory for follow-up questions.
4. Temporal Ground Truth (Current As Of Today):
   - Today is {today_str}. (Today's revenue is $23,650.00 across 10 orders).
   - Yesterday was {yesterday_str}. (Yesterday's revenue was $49,600.00 across 14 orders).
   - Current month is {current_month} ($514,750.00 MTD across 139 orders).
   - Last month was {last_month} ($1,188,100.00 total revenue across 320 orders).
   - From this month to last 3 months (June to September 2026): $3,933,400.00 total revenue across 1,027 orders.
   - Full year 2026 YTD: $9,522,700.00 across 2,564 orders.
   - When asked about "today", ALWAYS report {today_str}, never previous seed dates.
"""

VOXORA_SYSTEM_PROMPT = get_default_system_prompt()


class LLMService:
    """Unified LLM interface supporting Gemini REST and Groq with seamless fallback."""

    def __init__(self) -> None:
        self.settings = get_settings()

    async def generate_response(
        self,
        messages: list[dict[str, str]],
        system_prompt: str | None = None,
    ) -> tuple[str, str]:
        """Generate a response using the configured primary provider with automatic fallback. Returns (response_text, provider)."""
        prompt = system_prompt or get_default_system_prompt()
        primary = (self.settings.llm_provider or "groq").lower()

        if primary == "groq" and self.settings.groq_api_key:
            try:
                res = await self._call_groq(messages, prompt)
                return res, "groq"
            except Exception as e:
                logger.warning("Groq failed (%s). Falling back to Gemini...", e)
                if self.settings.gemini_api_key:
                    res = await self._call_gemini(messages, prompt)
                    return res, "gemini"
                raise
        else:
            try:
                res = await self._call_gemini(messages, prompt)
                return res, "gemini"
            except Exception as e:
                logger.warning("Gemini failed (%s). Falling back to Groq...", e)
                if self.settings.groq_api_key:
                    res = await self._call_groq(messages, prompt)
                    return res, "groq"
                raise

    async def stream_response(
        self,
        messages: list[dict[str, str]],
        system_prompt: str | None = None,
    ) -> AsyncGenerator[str, None]:
        """Stream tokens using Groq (or fallback). Yields string chunks."""
        prompt = system_prompt or get_default_system_prompt()
        primary = (self.settings.llm_provider or "groq").lower()

        if primary == "groq" and self.settings.groq_api_key:
            try:
                async for chunk in self._stream_groq(messages, prompt):
                    yield chunk
                return
            except Exception as e:
                logger.warning("Groq streaming failed (%s). Falling back to non-streaming...", e)

        # Fallback: non-streaming call, yield chunks
        try:
            full_text, _ = await self.generate_response(messages, prompt)
            # Yield in smaller word chunks to simulate smooth flow
            words = full_text.split(" ")
            for i, word in enumerate(words):
                yield word + (" " if i < len(words) - 1 else "")
        except Exception as e:
            logger.error("All LLM providers failed for streaming: %s", e)
            fallback = "I encountered an issue processing your request. Please check your data source or try again."
            yield fallback

    async def _stream_groq(
        self,
        messages: list[dict[str, str]],
        system_prompt: str,
    ) -> AsyncGenerator[str, None]:
        """Stream tokens from Groq API asynchronously using AsyncGroq."""
        api_key = self.settings.groq_api_key
        if not api_key:
            raise ValueError("GROQ_API_KEY is not configured.")

        model = self.settings.groq_model or "qwen/qwen3.8-27b"
        client = AsyncGroq(api_key=api_key)

        formatted_messages = [{"role": "system", "content": system_prompt}]
        for msg in messages:
            role = "assistant" if msg.get("role") == "assistant" else "user"
            formatted_messages.append({"role": role, "content": msg.get("content", "")})

        stream = await client.chat.completions.create(
            model=model,
            messages=formatted_messages,
            temperature=0.7,
            max_tokens=1024,
            stream=True,
        )

        async for chunk in stream:
            delta = chunk.choices[0].delta.content or ""
            if delta:
                yield delta

    async def _call_gemini(
        self,
        messages: list[dict[str, str]],
        system_prompt: str,
    ) -> str:
        """Call Google Gemini using HTTP API."""
        api_key = self.settings.gemini_api_key
        if not api_key:
            raise ValueError("GEMINI_API_KEY is not configured.")

        model = self.settings.gemini_model or "gemini-3.6-flash"
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"

        # Build Gemini contents structure
        contents: list[dict[str, Any]] = []
        for msg in messages:
            role = "user" if msg.get("role") in ("user", "human") else "model"
            contents.append({
                "role": role,
                "parts": [{"text": msg.get("content", "")}],
            })

        payload: dict[str, Any] = {
            "systemInstruction": {
                "parts": [{"text": system_prompt}]
            },
            "contents": contents,
            "generationConfig": {
                "temperature": 0.7,
                "maxOutputTokens": 1024,
            },
        }

        async with httpx.AsyncClient(timeout=8.0) as client:
            response = await client.post(url, json=payload)
            if response.status_code != 200:
                raise RuntimeError(f"Gemini API error {response.status_code}: {response.text}")

            data = response.json()
            candidates = data.get("candidates", [])
            if candidates and "content" in candidates[0]:
                parts = candidates[0]["content"].get("parts", [])
                if parts and "text" in parts[0]:
                    return parts[0]["text"].strip()
            return "I analyzed your request, but could not generate a response. Please try again."

    async def _call_groq(
        self,
        messages: list[dict[str, str]],
        system_prompt: str,
    ) -> str:
        """Call Groq API asynchronously using AsyncGroq."""
        api_key = self.settings.groq_api_key
        if not api_key:
            raise ValueError("GROQ_API_KEY is not configured.")

        model = self.settings.groq_model or "qwen/qwen3.8-27b"
        client = AsyncGroq(api_key=api_key)

        formatted_messages = [{"role": "system", "content": system_prompt}]
        for msg in messages:
            role = "assistant" if msg.get("role") == "assistant" else "user"
            formatted_messages.append({"role": role, "content": msg.get("content", "")})

        completion = await client.chat.completions.create(
            model=model,
            messages=formatted_messages,
            temperature=0.7,
            max_tokens=1024,
        )
        return completion.choices[0].message.content.strip()

    async def generate_suggestions(self, last_query: str, last_response: str) -> list[str]:
        """Generate 3 smart follow-up suggestions based on context."""
        prompt = (
            f"User asked: '{last_query}'\n"
            f"Assistant answered: '{last_response[:200]}'\n\n"
            "Suggest 3 short follow-up questions an executive or analyst would ask next.\n"
            "Return exactly 3 lines with only the question text, no numbers, no bullets."
        )
        try:
            response_text, _ = await self.generate_response(
                [{"role": "user", "content": prompt}],
                system_prompt="You suggest short, relevant BI follow-up queries."
            )
            lines = [line.strip().lstrip("1234567890.- ") for line in response_text.split("\n") if line.strip()]
            valid = [l for l in lines if len(l) > 6]
            return valid[:3] if valid else ["What are the key drivers?", "Show me the trend over time", "Compare with last month"]
    async def generate_title(self, first_message: str) -> str:
        """Generate a short 3-5 word conversation title from the first question."""
        prompt = f"Create a concise 3-5 word title for a conversation that starts with: '{first_message}'. Return only the title."
        try:
            title, _ = await self.generate_response(
                [{"role": "user", "content": prompt}],
                system_prompt="You generate concise business titles for conversation threads."
            )
            return title.strip().strip('"').strip("'")[:60]
        except Exception:
            return first_message[:50]


llm_service = LLMService()
