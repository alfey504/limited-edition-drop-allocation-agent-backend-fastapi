from collections.abc import AsyncGenerator

from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.config import Settings
from app.db.base import Base


def build_engine(settings: Settings) -> AsyncEngine:
    """Normalize a Neon connection string into one asyncpg + SQLAlchemy accept.

    Neon issues URLs like `postgres://user:pass@host/db?sslmode=require`.
    asyncpg's driver takes an `ssl` kwarg, not the libpq `sslmode` query
    param, so it has to be moved from the URL into `connect_args`.
    """
    url = make_url(settings.db_conn)

    if url.drivername in ("postgres", "postgresql"):
        url = url.set(drivername="postgresql+asyncpg")

    query = dict(url.query)
    connect_args: dict[str, str] = {}
    sslmode = query.pop("sslmode", None)
    if sslmode:
        connect_args["ssl"] = sslmode
    url = url.set(query=query)

    return create_async_engine(url, connect_args=connect_args, pool_pre_ping=True)


def build_session_factory(engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(bind=engine, expire_on_commit=False)


class Database:
    """Owns the engine + session factory for one application lifetime."""

    def __init__(self, settings: Settings) -> None:
        self.engine = build_engine(settings)
        self.session_factory = build_session_factory(self.engine)

    async def dispose(self) -> None:
        await self.engine.dispose()

    async def create_all(self) -> None:
        """Create tables from the current models. Temporary stand-in for
        Alembic migrations — call once at app startup."""
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    async def session(self) -> AsyncGenerator[AsyncSession, None]:
        async with self.session_factory() as session:
            yield session
