"""
Voxora Backend — Database session management.

Async SQLAlchemy engine and session factory.
"""

from typing import Any
from collections.abc import AsyncGenerator

from uuid import uuid4

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from app.config import get_settings

settings = get_settings()
db_url = settings.database_url

# Configure connection parameters:
# Supabase Transaction Pooler / PgBouncer does not support prepared statements properly.
# Disabling statement caches and generating unique statement names prevents DuplicatePreparedStatementError.
connect_args: dict[str, Any] = {
    "statement_cache_size": 0,
    "prepared_statement_cache_size": 0,
    "prepared_statement_name_func": lambda: f"__asyncpg_{uuid4()}__",
}
is_local = any(host in db_url for host in ("localhost", "127.0.0.1", "voxora-postgres"))
if not is_local:
    connect_args["ssl"] = "require"

# In serverless environments (e.g. Vercel), NullPool avoids connection leaks
engine = create_async_engine(
    db_url,
    connect_args=connect_args,
    echo=settings.database_echo,
    poolclass=NullPool,
)

async_session_factory = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency — yields an async database session."""
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
