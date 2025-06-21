# src/department_assistant/bot/handlers/direct_commands.py
from aiogram import Router
from aiogram.filters import Command, CommandObject
from aiogram.types import Message
import logging

# Импортируем наши функции проверки и новый сервис
from ...storage.database import check_postgres
from ...storage.s3_storage import check_minio
from ...services.faq_service import add_faq_entry

router = Router()


@router.message(Command("start"))
async def cmd_start(message: Message):
    await message.answer("Привет! Я DepartmentAssistant. Для проверки состояния систем используйте /healthcheck")


@router.message(Command("add_faq"))
async def cmd_add_faq(message: Message, command: CommandObject):
    if not command.args:
        await message.answer("Пожалуйста, укажите текст для добавления в базу знаний.\n"
                             "Пример: `/add_faq Какова форма отчета по командировкам?`")
        return

    faq_text = command.args
    try:
        await add_faq_entry(faq_text)
        await message.answer("✅ Новая информация успешно добавлена в базу знаний!")
    except Exception as e:
        # Логируем полную ошибку для себя
        logging.error(f"Failed to add FAQ entry: {e}", exc_info=True)
        # Отправляем пользователю простое и понятное сообщение
        await message.answer("❌ Произошла внутренняя ошибка при добавлении записи. Администратор уже уведомлен.")

@router.message(Command("healthcheck"))
async def cmd_healthcheck(message: Message):
    # Проверяем доступность сервисов
    is_postgres_ok = await check_postgres()
    is_minio_ok = await check_minio()

    # Формируем отчет
    postgres_status = "✅ OK" if is_postgres_ok else "❌ FAILED"
    minio_status = "✅ OK" if is_minio_ok else "❌ FAILED"

    report = (
        "<b>🩺 Health Check Report:</b>\n\n"
        f"PostgreSQL: {postgres_status}\n"
        f"MinIO (S3): {minio_status}"
    )

    await message.answer(report, parse_mode="HTML")