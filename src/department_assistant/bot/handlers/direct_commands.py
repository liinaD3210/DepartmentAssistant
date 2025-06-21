# src/department_assistant/bot/handlers/direct_commands.py
from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

# Импортируем наши функции проверки
from ...storage.database import check_postgres
from ...storage.s3_storage import check_minio

router = Router()

@router.message(Command("start"))
async def cmd_start(message: Message):
    await message.answer("Привет! Я DepartmentAssistant. Для проверки состояния систем используйте /healthcheck")

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