from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase
from app.DB.cread_db import username, password, db_name

DATABASE_URL = f"postgresql+asyncpg://{username}:{password}@localhost:5432/{db_name}"

async_engine = create_async_engine(DATABASE_URL, echo=True)

async_session_maker = async_sessionmaker(async_engine, expire_on_commit=False, class_=AsyncSession)

class Base(DeclarativeBase):
    pass