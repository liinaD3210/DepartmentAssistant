# src/department_assistant/services/llm_router.py
import logging
import json
from datetime import datetime, timedelta
import dateparser

import google.generativeai as genai

from ..core.config import settings
from ..core.models import Intent
from ..core.models import Intent, MeetingInfo


# Используем легковесную и быструю модель для классификации
# В будущем можно будет дообучить свою модель для большей точности
genai.configure(api_key=settings.gemini_api_key)
generation_model = genai.GenerativeModel('gemini-2.0-flash')

# Формируем список категорий для промпта
_CATEGORIES_TEXT = ", ".join([f'"{e.value}"' for e in Intent])

async def classify_intent(text: str) -> Intent:
    """
    Классифицирует текст сообщения в одну из предопределенных категорий (Intent).
    """
    prompt = f"""
    Классифицируй текст. Ответь ТОЛЬКО ОДНИМ СЛОВОМ из предложенного списка.
    
    Возможные категории: {_CATEGORIES_TEXT}.
    
    Текст для классификации:
    ---
    {text}
    ---
    
    Категория:
    """

    try:
        logging.info(f"Classifying text: '{text[:50]}...'")
        response = await generation_model.generate_content_async(prompt)
        
        # Убираем лишние пробелы и кавычки из ответа модели
        classified_intent_str = response.text.strip().replace('"', '')
        logging.info(f"LLM classification result: '{classified_intent_str}'")

        # Преобразуем строку в наш Enum.
        # Если модель вернет что-то не из списка, Intent._missing_ вернет IRRELEVANT
        intent = Intent(classified_intent_str)
        return intent

    except Exception as e:
        logging.error(f"Error during intent classification: {e}")
        # В случае любой ошибки считаем намерение нерелевантным
        return Intent.IRRELEVANT
    
async def extract_meeting_info(text: str) -> MeetingInfo | None:
    """Извлекает из текста дату, время и тему встречи, возвращая объект MeetingInfo."""
    # Получаем текущую дату и время для контекста
    now = datetime.now()
    prompt = f"""
    Извлеки из текста информацию о встрече: название (title), дату и время начала (start_time).
    Ответь ТОЛЬКО в формате JSON. Пример: {{"title": "Обсудить проект", "start_time": "2025-06-22 15:30:00"}}

    - Текущая дата и время для справки: {now.strftime('%Y-%m-%d %H:%M:%S')}.
    - Если время указано как "завтра в 10", используй завтрашнюю дату.
    - Если тема не указана, используй "Созвон".
    - Если не можешь извлечь дату или время, верни null.

    Текст для анализа:
    ---
    {text}
    ---
    JSON:
    """
    try:
        logging.info(f"Extracting meeting info from: '{text[:50]}...'")
        response = await generation_model.generate_content_async(prompt)
        
        # Убираем "мусор" вокруг JSON, который может вернуть модель
        json_str = response.text.strip().replace("```json", "").replace("```", "").strip()
        logging.info(f"LLM extraction result: {json_str}")

        data = json.loads(json_str)
        if not data or not data.get("start_time"):
            return None

        # Используем dateparser для надежного парсинга строки в datetime
        # settings={'PREFER_DATES_FROM': 'future'} помогает правильно понять "в 10:00"
        start_time = dateparser.parse(data["start_time"], settings={'PREFER_DATES_FROM': 'future', 'TIMEZONE': 'Europe/Moscow'})
        if not start_time:
            return None

        meeting = MeetingInfo(
            title=data.get("title", "Созвон"),
            start_time=start_time,
            end_time=start_time + timedelta(hours=1) # Длительность 1 час по умолчанию
        )
        return meeting

    except (json.JSONDecodeError, Exception) as e:
        logging.error(f"Failed to extract or parse meeting info: {e}")
        return None