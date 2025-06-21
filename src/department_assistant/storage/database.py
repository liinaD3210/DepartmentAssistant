# src/department_assistant/storage/database.py
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy.sql import text
from ..core.config import settings
import logging

# Создаем асинхронный "движок" для SQLAlchemy
engine = create_async_engine(settings.postgres_dsn)
# Фабрика для создания асинхронных сессий
async_session_maker = async_sessionmaker(engine, expire_on_commit=False)

async def check_postgres() -> bool:
    """Проверяет соединение с PostgreSQL."""
    try:
        async with engine.connect() as conn:
            # Выполняем простой запрос, чтобы убедиться, что соединение работает
            await conn.execute(text("SELECT 1"))
        logging.info("✅ PostgreSQL connection successful.")
        return True
    except Exception as e:
        logging.error(f"❌ PostgreSQL connection failed: {e}")
        return False