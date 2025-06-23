# src/department_assistant/bot/handlers/llm_flows.py

from aiogram import F, Router, Bot 
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery

from ...services.faq_service import find_similar_faq
from ...services.llm_router import classify_intent, Intent, extract_meeting_info
from ..keyboards import get_meeting_confirmation_keyboard, MeetingCallback
from ..states import MeetingProposal
from ...core.models import MeetingInfo # Импортируем нашу модель
from datetime import timedelta
from ...scheduler.scheduler import scheduler
from ...scheduler.scheduler import send_meeting_reminder
from ...services.llm_service import generate_answer_from_context
from ...services.llm_router import extract_task_info
from ...services.task_service import create_task
from ..keyboards import get_task_confirmation_keyboard, TaskCallback
from ..states import TaskProposal
from ...core.models import TaskInfo



router = Router()

# --- Новые хендлеры-заглушки ---
async def handle_task_creation(message: Message, state: FSMContext):
    task_info = await extract_task_info(message.text)
    if not task_info:
        return

    await state.update_data(proposed_task=task_info.model_dump_json())
    await state.set_state(TaskProposal.waiting_for_confirmation)

    # Формируем красивое сообщение для подтверждения
    response_lines = [f'Создать задачу "{task_info.title}"?']
    if task_info.deadline_str:
        response_lines.append(f"<b>Дедлайн:</b> {task_info.deadline_str}")
    if task_info.assignees:
        response_lines.append(f"<b>Ответственные:</b> {' '.join(task_info.assignees)}")
    
    await message.reply(
        "\n".join(response_lines),
        reply_markup=get_task_confirmation_keyboard()
    )

# --- Обработчики нажатия на кнопки ---
@router.callback_query(TaskProposal.waiting_for_confirmation, TaskCallback.filter(F.action == "confirm"))
async def process_task_confirmation(callback: CallbackQuery, state: FSMContext, bot: Bot):
    user_data = await state.get_data()
    proposed_task_info = TaskInfo.model_validate_json(user_data['proposed_task'])
    await state.clear()

    # Создаем задачу в БД
    created_task = await create_task(proposed_task_info, callback.message.chat.id, bot)

    # TODO: Добавить напоминание в APScheduler

    await callback.message.edit_text(f"✅ Задача \"{created_task.title}\" создана (ID: {created_task.id}).")
    await callback.answer()

@router.callback_query(TaskProposal.waiting_for_confirmation, TaskCallback.filter(F.action == "cancel"))
async def process_task_cancellation(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text("Действие отменено.")
    await callback.answer()

async def handle_meeting_creation(message: Message):
    await message.reply("Похоже, речь о встрече. Эта функция скоро появится.")

# --- Старый хендлер, который мы немного изменим ---
async def handle_faq_question(message: Message, question: str):
    # 1. Находим релевантный контекст
    context = await find_similar_faq(question)
    
    # 2. Генерируем ответ на основе контекста
    generated_answer = await generate_answer_from_context(question, context)
    
    # 3. Отправляем ответ пользователю
    await message.reply(generated_answer)



async def handle_meeting_creation(message: Message, state: FSMContext):
    meeting_info = await extract_meeting_info(message.text)
    
    if not meeting_info:
        # Модель не смогла извлечь данные, ничего не делаем
        return

    # Сохраняем предложенную встречу в состояние FSM
    # Pydantic модели не сериализуются по умолчанию, сохраняем как dict
    await state.update_data(proposed_meeting=meeting_info.model_dump_json())
    await state.set_state(MeetingProposal.waiting_for_confirmation)

    # Форматируем время для вывода
    start_str = meeting_info.start_time.strftime('%d.%m.%Y %H:%M')
    end_str = meeting_info.end_time.strftime('%H:%M')
    
    await message.reply(
        f"Создать встречу \"{meeting_info.title}\" на {start_str}–{end_str}?",
        reply_markup=get_meeting_confirmation_keyboard()
    )

# --- Обработчик нажатия на кнопку "Подтвердить" ---
@router.callback_query(MeetingProposal.waiting_for_confirmation, MeetingCallback.filter(F.action == "confirm"))
async def process_meeting_confirmation(callback: CallbackQuery, state: FSMContext, bot: Bot):
    user_data = await state.get_data()
    # Восстанавливаем объект MeetingInfo из JSON
    proposed_meeting = MeetingInfo.model_validate_json(user_data['proposed_meeting'])
    
    await state.clear() # Очищаем состояние

    # --- ЛОГИКА SCHEDULER ---
    # Напоминание за 5 минут до начала
    reminder_time = proposed_meeting.start_time - timedelta(minutes=5)
    
    # Добавляем задачу в планировщик
    scheduler.add_job(
        send_meeting_reminder,
        trigger='date',
        run_date=reminder_time,
        kwargs={
            'bot': bot,
            'chat_id': callback.message.chat.id,
            'title': proposed_meeting.title,
            'start_time_str': proposed_meeting.start_time.strftime('%H:%M')
        }
    )
    # -----------------------

    start_str = proposed_meeting.start_time.strftime('%d.%m.%Y %H:%M')
    await callback.message.edit_text(f"✅ Встреча \"{proposed_meeting.title}\" на {start_str} создана! Я напомню за 5 минут.")
    await callback.answer()

# --- Обработчик нажатия на кнопку "Отмена" ---
@router.callback_query(MeetingProposal.waiting_for_confirmation, MeetingCallback.filter(F.action == "cancel"))
async def process_meeting_cancellation(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text("Действие отменено.")
    await callback.answer()


# --- ГЛАВНЫЙ РОУТЕР-ХЕНДЛЕР ---
# ИЗМЕНЕНИЕ: Убираем .contains(), чтобы ловить ВСЕ сообщения
# Добавляем state: FSMContext в аргументы
@router.message(F.text)
async def main_llm_router(message: Message, state: FSMContext):
    # Если это ответ на сообщение бота или сообщение из канала, игнорируем
    if message.reply_to_message or message.forward_from_chat:
        return

    text = message.text
    if not text:
        return

    intent = await classify_intent(text)

    if intent == Intent.FAQ_QUESTION:
        # Для FAQ не нужно упоминание, но чтобы не спамить, можно добавить условие
        # Например, если сообщение содержит '?', 'как', 'почему' и т.д.
        if '?' in text or any(word in text.lower() for word in ['как', 'что', 'почему', 'где']):
             await handle_faq_question(message, question=text)
    elif intent == Intent.TASK_CREATION:
        await handle_task_creation(message, state)
    elif intent == Intent.MEETING_CREATION:
        await handle_meeting_creation(message, state)