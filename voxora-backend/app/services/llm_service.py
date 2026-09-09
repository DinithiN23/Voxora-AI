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
from groq import AsyncGroq, Groq

from app.config import get_settings

logger = logging.getLogger(__name__)

VOXORA_SYSTEM_PROMPT = """You are Voxora AI, an intelligent conversational business intelligence copilot.
Your job is to help business users understand their metrics, trends, sales, customer behavior, and operational KPIs.

Guidelines:
- Deliver clear, concise, executive-level answers.
- State the most important number or key metric first.
- Explain trends with context (e.g., "Up 8.7% compared to the same period last month").
- Maintain conversational memory: when the user asks follow-up questions (e.g. "Why did it increase?"), use the conversation history to understand the subject.
- If simulated data or general business reasoning is needed, provide realistic, sharp, actionable analysis.
- Use clean formatting with concise bullet points where appropriate.
"""


class LLMService:
    """Unified LLM interface supporting Gemini REST and Groq with seamless fallback."""

    def __init__(self) -> None:
        self.settings = get_settings()

    async def generate_response(
        self,
        messages: list[dict[str, str]],
        system_prompt: str | None = None,
    ) -> str:
        """Generate a response using the configured primary provider with automatic fallback."""
        prompt = system_prompt or VOXORA_SYSTEM_PROMPT
        primary = (self.settings.llm_provider or "groq").lower()

        if primary == "groq" and self.settings.groq_api_key:
            try:
                return await self._call_groq(messages, prompt)
            except Exception as e:
                logger.warning("Groq failed (%s). Falling back to Gemini...", e)
                if self.settings.gemini_api_key:
                    return await self._call_gemini(messages, prompt)
                raise
        else:
            try:
                return await self._call_gemini(messages, prompt)
            except Exception as e:
                logger.warning("Gemini failed (%s). Falling back to Groq...", e)
                if self.settings.groq_api_key:
                    return await self._call_groq(messages, prompt)
                raise

    async def stream_response(
        self,
        messages: list[dict[str, str]],
        system_prompt: str | None = None,
    ) -> AsyncGenerator[str, None]:
        """Stream tokens using Groq (or fallback). Yields string chunks."""
        prompt = system_prompt or VOXORA_SYSTEM_PROMPT
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
            full_text = await self.generate_response(messages, prompt)
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
            response_text = await self.generate_response(
                [{"role": "user", "content": prompt}],
                system_prompt="You suggest short, relevant BI follow-up queries."
            )
            lines = [line.strip().lstrip("1234567890.- ") for line in response_text.split("\n") if line.strip()]
            valid = [l for l in lines if len(l) > 6]
            return valid[:3] if valid else [
                "Break this down by region",
                "Why did this trend happen?",
                "Show forecast for next month",
            ]
        except Exception:
            return [
                "Break this down by region",
                "Why did this trend happen?",
                "Show forecast for next month",
            ]

    async def generate_title(self, first_message: str) -> str:
        """Generate a short 3-5 word conversation title from the first question."""
        prompt = f"Create a concise 3-5 word title for a conversation that starts with: '{first_message}'. Return only the title."
        try:
            title = await self.generate_response(
                [{"role": "user", "content": prompt}],
                system_prompt="You generate concise business titles for conversation threads."
            )
            return title.strip().strip('"').strip("'")[:60]
        except Exception:
            return first_message[:50]


llm_service = LLMService()
