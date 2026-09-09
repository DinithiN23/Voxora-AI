"""
Voxora Backend — Database Initialization Script.

Creates all database tables and verifies the PostgreSQL connection.
Run with: python -m app.db.init_db
"""

import asyncio
import sys
from sqlalchemy import text
from app.config import get_settings
from app.db.session import engine
from app.models import Base


async def init_db() -> None:
    settings = get_settings()
    # Mask password for display
    db_display_url = settings.database_url
    if "@" in db_display_url:
        prefix, host_part = db_display_url.split("@", 1)
        protocol_user = prefix.split(":", 2)
        if len(protocol_user) >= 3:
            db_display_url = f"{protocol_user[0]}:{protocol_user[1]}:****@{host_part}"

    if "YOUR_PASSWORD_HERE" in settings.database_url:
        print("\n⚠️  Please replace 'YOUR_PASSWORD_HERE' in `voxora-backend/.env` with your actual Supabase database password.", file=sys.stderr)
        print("   File: voxora-backend/.env -> Line 12", file=sys.stderr)
        sys.exit(1)

    print(f"🔌 Connecting to PostgreSQL at: {db_display_url}")

    try:
        async with engine.begin() as conn:
            # 1. Verify connection
            result = await conn.execute(text("SELECT version();"))
            pg_version = result.scalar()
            print(f" Connected: {pg_version}")

            # 2. Create tables
            print("📦 Creating database tables...")
            await conn.run_sync(Base.metadata.create_all)
            print(" All tables created / verified successfully:")
            for table_name in Base.metadata.tables.keys():
                print(f"   • {table_name}")

        print("\n🎉 PostgreSQL database is ready for Voxora AI!")

    except Exception as e:
        print(f"\n❌ Failed to connect to PostgreSQL: {e}", file=sys.stderr)
        print("\nTroubleshooting tips:", file=sys.stderr)
        print("  1. Make sure PostgreSQL is running (e.g. `docker compose up -d postgres` or `brew services start postgresql@16`)", file=sys.stderr)
        print("  2. Check DATABASE_URL in `voxora-backend/.env`", file=sys.stderr)
        sys.exit(1)
    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(init_db())
