"""
Voxora Backend — Text-to-SQL Engine.

Translates natural language questions into safe, optimized Google BigQuery SQL queries
with validation, sanitization, and safety sandboxing.
"""

import logging
import re
from typing import Any

from app.services.llm_service import llm_service
from app.services.semantic_layer import semantic_layer

logger = logging.getLogger(__name__)

FORBIDDEN_KEYWORDS = [
    r"\bDROP\b",
    r"\bDELETE\b",
    r"\bINSERT\b",
    r"\bUPDATE\b",
    r"\bALTER\b",
    r"\bTRUNCATE\b",
    r"\bCREATE\b",
    r"\bGRANT\b",
    r"\bREVOKE\b",
    r"\bEXEC\b",
    r"\bEXECUTE\b",
    r"\bMERGE\b",
]


class SQLValidationError(Exception):
    """Raised when generated SQL fails safety checks."""
    pass


class TextToSQLEngine:
    """Translates natural language to BigQuery SQL."""

    async def generate_sql(
        self,
        question: str,
        chat_history: list[dict[str, str]] | None = None,
    ) -> str:
        """
        Generate and validate a BigQuery SQL query from user question and history.
        """
        system_prompt = semantic_layer.get_system_prompt()

        messages: list[dict[str, str]] = []
        if chat_history:
            # Include recent turns for conversational context (e.g. follow-up questions)
            for m in chat_history[-4:]:
                messages.append({"role": m.get("role", "user"), "content": m.get("content", "")})

        # Add the target query
        messages.append({
            "role": "user",
            "content": f"Write a BigQuery SQL query to answer this business question:\n'{question}'"
        })

        # Call LLM
        response = await llm_service.generate_response(messages, system_prompt=system_prompt)

        # Extract and sanitize SQL
        cleaned_sql = self._clean_and_sanitize(response)

        # Validate SQL safety
        self._validate_sql(cleaned_sql)

        return cleaned_sql

    def _clean_and_sanitize(self, raw_output: str) -> str:
        """Extract SQL from markdown fencing and format."""
        # Find ```sql ... ``` or ``` ... ```
        sql_match = re.search(r"```(?:sql)?\s*([\s\S]*?)\s*```", raw_output, re.IGNORECASE)
        if sql_match:
            sql = sql_match.group(1).strip()
        else:
            sql = raw_output.strip()

        # Remove trailing semicolons
        sql = sql.rstrip(";")

        # Inject LIMIT 100 if neither LIMIT nor aggregation with single row is present
        if not re.search(r"\bLIMIT\b", sql, re.IGNORECASE):
            sql = f"{sql}\nLIMIT 100"

        return sql

    def _validate_sql(self, sql: str) -> None:
        """Verify that the SQL query is strictly read-only and safe."""
        sql_upper = sql.upper().strip()

        # Must begin with SELECT or WITH
        if not (sql_upper.startswith("SELECT") or sql_upper.startswith("WITH")):
            raise SQLValidationError("Only read-only SELECT queries are allowed.")

        # Check for forbidden mutations
        for pattern in FORBIDDEN_KEYWORDS:
            if re.search(pattern, sql_upper):
                raise SQLValidationError(f"Query contains forbidden operation matching pattern {pattern}")


text_to_sql_engine = TextToSQLEngine()
