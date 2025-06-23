# src/department_assistant/services/task_service.py
import logging
from datetime import datetime
import dateparser

from ..storage.database import async_session_maker
from ..storage.models.task import Task
from ..core.models import TaskInfo
from ..scheduler.scheduler import scheduler, send_task_reminder # Импортируем
from aiogram import Bot # Импортируем для type hint
from sqlalchemy import select, update


# Список слов, которые нужно удалить
PREPOSITIONS_TO_CLEAN = ["до ", "к ", "до конца "]

async def create_task(task_info: TaskInfo, chat_id: int, bot: Bot) -> Task:
    """Сохраняет новую задачу в БД и возвращает созданный объект."""
    deadline = None
    if task_info.deadline_str:
        clean_deadline_str = task_info.deadline_str.lower()
        # Удаляем предлоги из начала строки
        for prep in PREPOSITIONS_TO_CLEAN:
            if clean_deadline_str.startswith(prep):
                clean_deadline_str = clean_deadline_str[len(prep):]
        
        logging.info(f"Parsing cleaned deadline string: '{clean_deadline_str}'")

        # Устанавливаем конец дня как дедлайн, если время не указано
        deadline = dateparser.parse(
            clean_deadline_str,
            settings={'PREFER_DATES_FROM': 'future', 'TIMEZONE': 'Europe/Moscow', 'RETURN_AS_TIMEZONE_AWARE': True}
        )
        if deadline and not ("час" in clean_deadline_str or ":" in clean_deadline_str):
             # Если время не было явно указано, ставим конец рабочего дня
            deadline = deadline.replace(hour=23, minute=59, second=59)

    new_task = Task(
        title=task_info.title,
        assignees=" ".join(task_info.assignees) if task_info.assignees else None,
        deadline=deadline,
        chat_id=chat_id
    )

    async with async_session_maker() as session:
        session.add(new_task)
        await session.commit()
        await session.refresh(new_task)

    logging.info(f"Task {new_task.id} created: {new_task.title}")

    # --- Установка напоминания ---
    if new_task.deadline:
        # Напоминание в день дедлайна в 10:00 утра
        reminder_time = new_task.deadline.replace(hour=10, minute=0, second=0, microsecond=0)
        
        # Если 10 утра уже прошло сегодня, то не напоминаем
        if reminder_time > datetime.now(reminder_time.tzinfo):
            scheduler.add_job(
                send_task_reminder,
                trigger='date',
                run_date=reminder_time,
                id=f"task_reminder_{new_task.id}", # Уникальный ID для задачи
                kwargs={
                    'bot': bot,
                    'chat_id': new_task.chat_id,
                    'task_id': new_task.id,
                    'title': new_task.title,
                    'assignees': new_task.assignees
                }
            )
            logging.info(f"Reminder for task {new_task.id} scheduled at {reminder_time}")

    return new_task

async def get_active_tasks_for_chat(chat_id: int) -> list[Task]:
    """Возвращает список активных задач для указанного чата."""
    query = (
        select(Task)
        .where(Task.chat_id == chat_id, Task.is_completed == False)
        .order_by(Task.deadline.asc().nulls_last(), Task.id.asc()) # Сортируем по дедлайну
    )
    async with async_session_maker() as session:
        result = await session.execute(query)
        return result.scalars().all()

async def close_task(task_id: int, chat_id: int) -> Task | None:
    """Закрывает задачу по ID и удаляет напоминание."""
    # Сначала найдем задачу, чтобы убедиться, что она принадлежит этому чату
    query = select(Task).where(Task.id == task_id, Task.chat_id == chat_id)
    
    async with async_session_maker() as session:
        result = await session.execute(query)
        task_to_close = result.scalar_one_or_none()

        if not task_to_close or task_to_close.is_completed:
            return None # Задача не найдена или уже закрыта

        # Обновляем статус
        update_query = (
            update(Task)
            .where(Task.id == task_id)
            .values(is_completed=True)
        )
        await session.execute(update_query)
        await session.commit()
    
    # Удаляем напоминание из планировщика, если оно есть
    reminder_id = f"task_reminder_{task_id}"
    if scheduler.get_job(reminder_id):
        scheduler.remove_job(reminder_id)
        logging.info(f"Removed reminder for closed task {task_id}")

    return task_to_close