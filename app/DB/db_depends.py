from sqlalchemy.ext.asyncio import AsyncSession 
from collections.abc import AsyncGenerator

from app.DB.database import async_session_maker

async def get_async_db() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_maker() as session:
        yield session