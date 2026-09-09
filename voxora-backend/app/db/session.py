"""
Voxora Backend — Database session management.

Async SQLAlchemy engine and session factory.
"""

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config import get_settings

settings = get_settings()
db_url = settings.database_url

# Configure SSL for remote cloud databases (Neon, Supabase, Cloud SQL, AWS RDS, etc.)
connect_args: dict[str, str] = {}
is_local = any(host in db_url for host in ("localhost", "127.0.0.1", "voxora-postgres"))
if not is_local:
    connect_args["ssl"] = "require"

engine = create_async_engine(
    db_url,
    connect_args=connect_args,
    echo=settings.database_echo,
    pool_size=20,
    max_overflow=10,
    pool_pre_ping=True,
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
