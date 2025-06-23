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

async def find_similar_faq(query_text: str) -> list[str]: # <--- Меняем возвращаемый тип на list[str]
    """Находит несколько наиболее похожих записей в FAQ."""
    logging.info(f"Searching for top 3 FAQ entries similar to: {query_text[:50]}...")
    query_embedding = await llm_service.get_query_embedding(query_text)

    async with async_session_maker() as session:
        # Ищем 3 самых близких по L2-дистанции вектора
        result = await session.execute(
            select(FaqEntry.text)
            .order_by(FaqEntry.embedding.l2_distance(query_embedding))
            .limit(3) # <--- Увеличиваем лимит
        )
        # .all() вернет список кортежей, .scalars() развернет их в список строк
        found_texts = result.scalars().all()

    if found_texts:
        logging.info(f"Found {len(found_texts)} similar FAQ entries.")
    else:
        logging.warning("No similar FAQ found.")

    return found_texts # <--- Возвращаем список