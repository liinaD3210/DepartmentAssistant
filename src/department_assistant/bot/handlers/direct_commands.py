# src/department_assistant/bot/handlers/direct_commands.py
from aiogram import Router
from aiogram.filters import Command, CommandObject
from aiogram.types import Message
import logging
from aiogram import F, Router, Bot  # <--- ДОБАВЛЯЕМ F СЮДА
import io  
from pathlib import Path 

# Импортируем наши функции проверки и новый сервис
from ...storage.database import check_postgres
from ...storage.s3_storage import check_minio
from ...services.faq_service import add_faq_entry
from ...services.document_parser import parse_document
from ...storage.s3_storage import minio_client
from ...services.task_service import get_active_tasks_for_chat, close_task
from datetime import datetime

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

@router.message(F.document & F.caption)
async def handle_document_upload(message: Message, bot: Bot):
    if not message.caption.lower().startswith("загрузить в базу"):
        return # Реагируем только на явную команду в подписи

    document = message.document
    file_info = await bot.get_file(document.file_id)
    file_content = await bot.download_file(file_info.file_path)
    
    file_path = Path(document.file_name)
    
    await message.reply(f"📄 Получил файл '{file_path.name}'. Начинаю обработку...")

    # 1. Сохраняем файл в MinIO
    bucket_name = "documents"
    # Проверяем, существует ли бакет, и создаем, если нет
    if not minio_client.bucket_exists(bucket_name):
        minio_client.make_bucket(bucket_name)

    minio_client.put_object(
        bucket_name=bucket_name,
        object_name=file_path.name,
        data=io.BytesIO(file_content.read()),
        length=file_info.file_size
    )
    
    # 2. Парсим документ и разбиваем на чанки
    chunks = parse_document(file_path, file_content.getvalue())
    if not chunks:
        await message.reply("Не удалось извлечь текст из файла или тип файла не поддерживается.")
        return

    # 3. Добавляем каждый чанк в базу знаний
    try:
        for i, chunk in enumerate(chunks):
            # Добавляем к тексту чанка метаданные об источнике
            chunk_with_source = f"Источник: {file_path.name}\n\n{chunk}"
            await add_faq_entry(chunk_with_source)
        
        await message.reply(f"✅ Файл '{file_path.name}' успешно обработан и добавлен в базу знаний ({len(chunks)} фрагментов).")
    except Exception as e:
        await message.reply(f"❌ Произошла ошибка при добавлении фрагментов в базу: {e}")

@router.message(Command("tasks"))
async def cmd_tasks(message: Message):
    tasks = await get_active_tasks_for_chat(message.chat.id)
    if not tasks:
        await message.reply("🎉 Все задачи выполнены! Отличная работа!")
        return

    response_lines = ["<b>📝 Активные задачи:</b>\n"]
    for task in tasks:
        deadline_str = ""
        if task.deadline:
            is_overdue = task.deadline < datetime.now(task.deadline.tzinfo)
            # Форматируем дату
            deadline_formatted = task.deadline.strftime('%d.%m.%Y')
            deadline_str = f" (до {deadline_formatted}){'❗️' if is_overdue else ''}"

        assignees_str = f" {task.assignees}" if task.assignees else ""
        # Используем тег <code> для ID задачи
        response_lines.append(f"• <code>#{task.id}</code>: {task.title}{assignees_str}{deadline_str}")
    
    # Меняем parse_mode на HTML
    await message.reply("\n".join(response_lines), parse_mode="HTML")


@router.message(Command("close"))
async def cmd_close_task(message: Message, command: CommandObject):
    if not command.args or not command.args.isdigit():
        await message.reply("Пожалуйста, укажите ID задачи, которую хотите закрыть.\nПример: `/close 42`")
        return
    
    task_id = int(command.args)
    closed_task = await close_task(task_id, message.chat.id)

    if closed_task:
        await message.reply(f"✅ Задача `#{task_id}`: \"{closed_task.title}\" закрыта.")
    else:
        await message.reply(f"Не удалось найти активную задачу с ID `#{task_id}` в этом чате.")