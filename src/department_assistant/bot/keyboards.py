# src/department_assistant/bot/keyboards.py

from aiogram.filters.callback_data import CallbackData
from aiogram.types import InlineKeyboardMarkup # Важно использовать InlineKeyboardMarkup для возврата
from aiogram.utils.keyboard import InlineKeyboardBuilder

# Используем CallbackData для передачи данных в кнопках
class MeetingCallback(CallbackData, prefix="meeting"):
    action: str # 'confirm' или 'cancel'

# Убедитесь, что имя функции ТОЧНО такое
def get_meeting_confirmation_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(
        text="✅ Подтвердить",
        callback_data=MeetingCallback(action="confirm").pack()
    )
    builder.button(
        text="❌ Отмена",
        callback_data=MeetingCallback(action="cancel").pack()
    )
    # as_markup() возвращает правильный тип для reply_markup
    return builder.as_markup()