# src/department_assistant/bot/handlers/llm_flows.py

from aiogram import F, Router # <--- Убедитесь, что Router импортирован
from aiogram.types import Message

from ...services.faq_service import find_similar_faq

router = Router() # <--- ВОТ ЭТА СТРОКА, СКОРЕЕ ВСЕГО, ОТСУТСТВУЕТ

# Этот хендлер будет срабатывать на сообщения, где упомянули бота
@router.message(F.text.contains("@DepartmentAssistBot"))
async def answer_faq_question(message: Message):
    # Убираем упоминание бота из текста вопроса
    # Снова, лучше использовать getMe или конфиг, но для теста сойдет
    question = message.text.replace("@DepartmentAssistBot", "").strip()
    
    if not question:
        return

    answer = await find_similar_faq(question)

    if answer:
        # MVP: Просто отвечаем найденным текстом
        response = f"Возможно, вы имели в виду:\n\n---\n{answer}"
    else:
        # В будущем здесь будет запускаться Learn-flow
        response = "К сожалению, я не нашел ответа на ваш вопрос в базе знаний."

    await message.reply(response)