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
        tenant_id: str | None = None,
    ) -> tuple[str, str]:
        """
        Generate and validate a BigQuery SQL query from user question and history. Returns (sql, provider).
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
        response, provider = await llm_service.generate_response(messages, system_prompt=system_prompt)

        # Extract and sanitize SQL
        cleaned_sql = self._clean_and_sanitize(response)

        # Validate SQL safety and inject tenant_id via AST
        final_sql = self._validate_and_enforce_ast(cleaned_sql, tenant_id)

        return final_sql, provider

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

    def _validate_and_enforce_ast(self, sql: str, tenant_id: str | None) -> str:
        """Verify that the SQL query is strictly read-only and safe via AST, and force inject tenant scope."""
        import sqlglot
        from sqlglot import exp

        try:
            parsed = sqlglot.parse_one(sql, dialect="bigquery")
        except Exception as e:
            raise SQLValidationError(f"Query parsing failed: {e}")

        # AST Allowlist 1: Must be a SELECT statement
        if not isinstance(parsed, exp.Select):
            raise SQLValidationError("Only read-only SELECT queries are allowed.")

        # Require a WHERE clause in the original text to prevent full table scans on time (before tenant inject)
        if "WHERE" not in sql.upper():
            raise SQLValidationError("Query must include a WHERE clause with a date-range or partition filter to prevent full table scans.")

        # AST Allowlist 2: Verify only allowed tables are accessed
        ALLOWED_TABLES = {"orders", "products", "customers", "daily_kpis"}
        for table in parsed.find_all(exp.Table):
            table_name = table.name.lower()
            if table_name not in ALLOWED_TABLES:
                raise SQLValidationError(f"Query attempts to access unauthorized table: {table_name}")

        # Inject tenant isolation logic
        if tenant_id:
            # Add AND tenant_id = '...'
            tenant_cond = f"tenant_id = '{tenant_id}'"
            parsed = parsed.where(tenant_cond)

        return parsed.sql(dialect="bigquery")


text_to_sql_engine = TextToSQLEngine()
