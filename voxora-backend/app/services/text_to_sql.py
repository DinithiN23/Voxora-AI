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


class GeneratedSQL(tuple):
    """
    Tuple subclass returning (sql, provider) while preserving .was_auto_scoped metadata
    for backward compatibility with callers expecting a 2-tuple.
    """
    sql: str
    provider: str
    was_auto_scoped: bool

    def __new__(cls, sql: str, provider: str, was_auto_scoped: bool = False):
        instance = super().__new__(cls, (sql, provider))
        instance.sql = sql
        instance.provider = provider
        instance.was_auto_scoped = was_auto_scoped
        return instance


class TextToSQLEngine:
    """Translates natural language to BigQuery SQL."""

    async def generate_sql(
        self,
        question: str,
        chat_history: list[dict[str, str]] | None = None,
        tenant_id: str | None = None,
    ) -> GeneratedSQL:
        """
        Generate and validate a BigQuery SQL query from user question and history.
        Returns GeneratedSQL(sql, provider, was_auto_scoped) which unpacks as (sql, provider).
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

        # Validate SQL safety, verify date scoping via AST, and auto-inject safe default if un-scoped
        final_sql, was_auto_scoped = self._validate_and_enforce_ast(cleaned_sql, tenant_id)

        return GeneratedSQL(final_sql, provider, was_auto_scoped)

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

    def _validate_and_enforce_ast(self, sql: str, tenant_id: str | None = None) -> tuple[str, bool]:
        """
        Verify that the SQL query is strictly read-only and safe via AST.
        Inspects the WHERE clause for date-scoping columns (order_date, date, created_at).
        If no temporal filter is present, auto-injects a safe default (last 30 days) to prevent
        unintended full-table scans.
        """
        try:
            import sqlglot
            from sqlglot import exp
            has_sqlglot = True
        except ImportError:
            has_sqlglot = False
            logger.warning("sqlglot is not installed; falling back to safe regex SQL validation")

        if not has_sqlglot:
            clean_sql = sql.strip().rstrip(";")
            upper = clean_sql.upper()
            if not upper.startswith("SELECT"):
                raise SQLValidationError("Only read-only SELECT queries are allowed.")
            forbidden = ["DROP ", "DELETE ", "UPDATE ", "INSERT ", "ALTER ", "TRUNCATE ", "CREATE "]
            for word in forbidden:
                if word in upper:
                    raise SQLValidationError(f"Query contains forbidden keyword: {word.strip()}")
            return clean_sql, False

        try:
            parsed = sqlglot.parse_one(sql, dialect="bigquery")
        except Exception as e:
            raise SQLValidationError(f"Query parsing failed: {e}")

        # AST Allowlist 1: Must be a SELECT statement
        if not isinstance(parsed, exp.Select):
            raise SQLValidationError("Only read-only SELECT queries are allowed.")

        # AST Allowlist 2: Verify only allowed tables are accessed
        ALLOWED_TABLES = {"orders", "products", "customers", "daily_kpis"}
        tables_found = set()
        for table in parsed.find_all(exp.Table):
            table_name = table.name.lower()
            if table_name not in ALLOWED_TABLES:
                raise SQLValidationError(f"Query attempts to access unauthorized table: {table_name}")
            tables_found.add(table_name)

        # AST Date Scoping Validation: Check for presence of date/temporal filters
        DATE_COLUMNS = {"order_date", "date", "created_at"}
        has_date_filter = False
        where_clause = parsed.find(exp.Where)
        if where_clause:
            for col in where_clause.find_all(exp.Column):
                if col.name.lower() in DATE_COLUMNS:
                    has_date_filter = True
                    break

        was_auto_scoped = False
        if not has_date_filter:
            # Determine appropriate temporal column based on queried tables
            if "daily_kpis" in tables_found and "orders" not in tables_found:
                default_cond = sqlglot.parse_one("date >= DATE_SUB(CURRENT_DATE(), INTERVAL 30 DAY)", dialect="bigquery")
            else:
                default_cond = sqlglot.parse_one("order_date >= DATE_SUB(CURRENT_DATE(), INTERVAL 30 DAY)", dialect="bigquery")

            parsed = parsed.where(default_cond)
            was_auto_scoped = True
            logger.info("Un-scoped query detected. Auto-injected 30-day default filter to prevent full scan.")

        return parsed.sql(dialect="bigquery"), was_auto_scoped


text_to_sql_engine = TextToSQLEngine()
