# src/department_assistant/services/faq_service.py
import logging
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from . import llm_service # Импортируем весь модуль
from ..storage.database import async_session_maker
from ..storage.models.faq import FaqEntry

async def add_faq_entry(text: str):
    """Добавляет новую запись в базу знаний FAQ."""
    logging.info(f"Adding new FAQ entry: {text[:50]}...")
    # Используем функцию для документов
    embedding = await llm_service.get_text_embedding(text)

    async with async_session_maker() as session:
        faq_item = FaqEntry(text=text, embedding=embedding)
        session.add(faq_item)
        await session.commit()
    logging.info("Successfully added new FAQ entry.")

async def find_similar_faq(query_text: str) -> str | None:
    """Находит наиболее похожую запись в FAQ."""
    logging.info(f"Searching for FAQ similar to: {query_text[:50]}...")
    # Используем функцию для поисковых запросов
    query_embedding = await llm_service.get_query_embedding(query_text)

    async with async_session_maker() as session:
        result = await session.execute(
            select(FaqEntry.text)
            .order_by(FaqEntry.embedding.l2_distance(query_embedding))
            .limit(1)
        )
        found_text = result.scalar_one_or_none()

    if found_text:
        logging.info(f"Found similar FAQ: {found_text[:50]}...")
    else:
        logging.warning("No similar FAQ found.")

    return found_text