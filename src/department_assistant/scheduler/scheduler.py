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

async def send_task_reminder(bot: Bot, chat_id: int, task_id: int, title: str, assignees: str | None):
    """Отправляет напоминание о дедлайне задачи."""
    message_lines = [f"🔥🔥 **ДЕДЛАЙН СЕГОДНЯ!** 🔥🔥"]
    message_lines.append(f"\nЗадача #{task_id}: {title}")
    if assignees:
        message_lines.append(f"Ответственные: {assignees}")
    
    await bot.send_message(
        chat_id=chat_id,
        text="\n".join(message_lines)
    )