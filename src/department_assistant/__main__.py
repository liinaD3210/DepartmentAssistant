# src/department_assistant/__main__.py
import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from .core.config import settings
from .bot.handlers import direct_commands, llm_flows
from .scheduler.scheduler import scheduler

async def main():
    logging.basicConfig(level=logging.INFO)

    # 2. Используем новый синтаксис для настроек по умолчанию
    bot = Bot(
        token=settings.bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )

    scheduler.start()
    
    dp = Dispatcher()

    # Подключаем роутеры
    dp.include_router(direct_commands.router)
    dp.include_router(llm_flows.router)

    # Удаляем вебхук, если он был установлен ранее
    await bot.delete_webhook(drop_pending_updates=True)
    # Запускаем polling
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())