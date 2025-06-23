# src/department_assistant/scheduler/scheduler.py
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from aiogram import Bot

# Создаем единственный экземпляр планировщика
scheduler = AsyncIOScheduler(timezone="Europe/Moscow")

# --- Функция-задача, которую будет вызывать планировщик ---
async def send_meeting_reminder(bot: Bot, chat_id: int, title: str, start_time_str: str):
    """Отправляет напоминание о встрече."""
    await bot.send_message(
        chat_id=chat_id,
        text=f"🔔 **Напоминание!**\n\nВстреча \"{title}\" начнется в {start_time_str}."
    )