from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from core.config import settings
from app.database import Base

# We use the existing Base from app.database to ensure all models are registered
# But we create a new async engine for high-concurrency WebSocket persistence

def _build_connect_args(url: str) -> dict:
    if "sqlite" in url:
        return {"check_same_thread": False}
    if "asyncpg" in url:
        return {"ssl": True} if "sslmode" in url else {}
    return {}

def _clean_url(url: str) -> str:
    """Strip psycopg2-style SSL params that asyncpg doesn't accept."""
    from urllib.parse import urlparse, urlencode, parse_qs, urlunparse
    parsed = urlparse(url)
    params = parse_qs(parsed.query, keep_blank_values=True)
    for key in ("sslmode", "channel_binding"):
        params.pop(key, None)
    new_query = urlencode({k: v[0] for k, v in params.items()})
    return urlunparse(parsed._replace(query=new_query))

_db_url = _clean_url(settings.DATABASE_URL)

engine = create_async_engine(
    _db_url,
    echo=False,
    connect_args=_build_connect_args(settings.DATABASE_URL),
)

AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

async def get_async_db():
    """Dependency that provides an async database session."""
    async with AsyncSessionLocal() as session:
        yield session
