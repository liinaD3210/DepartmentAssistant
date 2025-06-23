# src/department_assistant/services/llm_service.py
import logging
import google.generativeai as genai
from ..core.config import settings

# Конфигурируем API с ключом из настроек
genai.configure(api_key=settings.gemini_api_key)

# Указываем правильное, полное имя модели для эмбеддингов
EMBEDDING_MODEL_NAME = "models/embedding-001"
generation_model = genai.GenerativeModel('gemini-1.5-flash')

async def get_text_embedding(text: str) -> list[float]:
    """Получает векторное представление (эмбеддинг) для текста."""
    logging.info(f"Requesting embedding for text: '{text[:30]}...'")
    try:
        # Gemini API синхронный, для высоких нагрузок стоит выносить в ThreadPoolExecutor,
        # но для начала aiogram справится и так.
        response = genai.embed_content(
            model=EMBEDDING_MODEL_NAME, # <--- Исправленное имя
            content=text,
            task_type="RETRIEVAL_DOCUMENT" # 'RETRIEVAL_DOCUMENT' для текстов, которые мы сохраняем в базу
        )
        logging.info("Successfully received embedding.")
        return response['embedding']
    except Exception as e:
        logging.error(f"Failed to get embedding from Gemini: {e}")
        # Пробрасываем исключение дальше, чтобы хендлер мог его поймать и сообщить пользователю
        raise

# Также обновим функцию поиска, чтобы она использовала правильную task_type
async def get_query_embedding(text: str) -> list[float]:
    """Получает векторное представление (эмбеддинг) для ПОИСКОВОГО ЗАПРОСА."""
    logging.info(f"Requesting embedding for query: '{text[:30]}...'")
    try:
        response = genai.embed_content(
            model=EMBEDDING_MODEL_NAME,
            content=text,
            task_type="RETRIEVAL_QUERY" # 'RETRIEVAL_QUERY' для текстов, по которым мы ищем
        )
        logging.info("Successfully received query embedding.")
        return response['embedding']
    except Exception as e:
        logging.error(f"Failed to get query embedding from Gemini: {e}")
        raise

async def generate_answer_from_context(question: str, context: list[str]) -> str:
    """Генерирует ответ на основе вопроса и найденного контекста."""
    if not context:
        return "К сожалению, я не нашел информации по вашему вопросу в базе знаний."

    # Соединяем найденные фрагменты в один большой текст контекста
    context_str = "\n---\n".join(context)

    prompt = f"""
    Ты — вежливый и полезный ИИ-ассистент в компании.
    Твоя задача — ответить на вопрос пользователя, основываясь ИСКЛЮЧИТЕЛЬНО на предоставленном ниже контексте.
    Не придумывай ничего от себя. Если в контексте нет прямого ответа, вежливо сообщи, что не можешь ответить.
    Отвечай от первого лица (например, "Я нашел, что...").

    **Контекст из базы знаний:**
    {context_str}

    **Вопрос пользователя:**
    {question}

    **Твой ответ:**
    """
    
    try:
        logging.info(f"Generating answer for question: '{question[:50]}...'")
        response = await generation_model.generate_content_async(prompt)
        logging.info("Successfully generated answer.")
        return response.text
    except Exception as e:
        logging.error(f"Error during answer generation: {e}")
        return "Произошла ошибка при генерации ответа. Пожалуйста, попробуйте позже."