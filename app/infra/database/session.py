from datetime import datetime

from app.config import ENGINE, TIMEZONE
from app.infra.database.models import Base
from sqlalchemy import text
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

engine = create_async_engine(url=ENGINE, echo=False, pool_size=20)
async_session = async_sessionmaker(engine)


async def run_database(reset: bool):
    async with engine.begin() as conn:
        if reset and "asyncpg" in ENGINE:
            tables = list(Base.metadata.tables.keys())
            for table in tables:
                await conn.execute(text(f"DROP TABLE IF EXISTS {table} CASCADE;"))

        if TIMEZONE and "asyncpg" in ENGINE:
            await conn.execute(
                text(
                    f"SET TIME ZONE 'UTC{datetime.now(TIMEZONE).utcoffset().total_seconds() / 3600:+.0f}';"
                )
            )

        await conn.run_sync(Base.metadata.create_all)

    from app.infra.database.init_db import init
    await init()
