# seed_db.py
import asyncio
from pathlib import Path
from datetime import datetime, timedelta

# Убедитесь, что этот скрипт запускается из корневой папки проекта
try:
    from src.department_assistant.storage.database import async_session_maker
    from src.department_assistant.storage.models.faq import FaqEntry
    from src.department_assistant.storage.models.task import Task
    from src.department_assistant.services.document_parser import parse_document
    from src.department_assistant.services.llm_service import get_text_embedding
except ImportError:
    import sys
    sys.path.append('.')
    from src.department_assistant.storage.database import async_session_maker
    from src.department_assistant.storage.models.faq import FaqEntry
    from src.department_assistant.storage.models.task import Task
    from src.department_assistant.services.document_parser import parse_document
    from src.department_assistant.services.llm_service import get_text_embedding


DEMO_CHAT_ID = -100123456789  # Тот же ID, что и в демо-приложении

# --- Тексты для наших "документов" в базе знаний ---

COMPANY_REGULATIONS = """
### Регламент по рабочим процессам в компании "Innovate Forward Inc."

**1. Порядок оформления отпусков**
Для оформления ежегодного оплачиваемого отпуска сотрудник должен подать заявление не позднее, чем за 14 календарных дней до предполагаемой даты начала отпуска. Заявление подается через корпоративный портал "MyForward" в разделе "Кадровые сервисы".

**2. Процедура заказа оборудования**
Если сотруднику требуется новое оборудование (ноутбук, монитор), необходимо создать заявку в системе "IT HelpDesk". Стандартная модель рабочего ноутбука в компании - "DeltaBook Pro 14".

**3. Политика информационной безопасности: Пароли**
Сотрудники обязаны использовать сложные пароли. Смена пароля является обязательной каждые 90 дней. Запрещается записывать пароли на стикерах.
"""

SECURITY_POLICY = """
### Политика безопасности и доступов "Innovate Forward Inc."

**Раздел А: Доступ к облачным хранилищам**
Для доступа к S3-хранилищу 'omega-assets', где хранятся все графические исходники и макеты, теперь требуется обязательное подключение через корпоративный VPN 'Innovate-Secure'. Прямое подключение из внешней сети было заблокировано с 25.06.2025 по соображениям безопасности. Убедитесь, что ваш VPN-клиент обновлен до последней версии.
"""


async def seed_database():
    """
    Наполняет базу данных демонстрационными данными: регламентами и задачами.
    Эта функция идемпотентна: она сначала удаляет старые демо-данные, а потом создает новые.
    """
    print("🌱 Начинаем наполнение базы данных для демо-версии...")

    async with async_session_maker() as session:
        # --- 1. Очищаем старые демо-данные ---
        print("🗑️  Очистка старых демонстрационных данных...")
        await session.execute(FaqEntry.__table__.delete())
        await session.execute(Task.__table__.delete().where(Task.chat_id == DEMO_CHAT_ID))
        await session.commit() # Фиксируем удаление
        
        # --- 2. Наполняем базу знаний (FAQ) ---
        print("📄 Парсинг и векторизация документов...")
        
        documents_to_seed = {
            "Регламент_Компании.txt": COMPANY_REGULATIONS,
            "Регламент_Безопасности.txt": SECURITY_POLICY # Добавляем новый документ
        }
        
        total_chunks = 0
        for doc_name, doc_content in documents_to_seed.items():
            chunks = parse_document(Path(doc_name), doc_content.encode('utf-8'))
            for chunk in chunks:
                chunk_with_source = f"Источник: {doc_name}\n\n{chunk}"
                embedding = await get_text_embedding(chunk_with_source)
                faq_entry = FaqEntry(text=chunk_with_source, embedding=embedding)
                session.add(faq_entry)
            total_chunks += len(chunks)
        
        print(f"✅ База знаний наполнена {total_chunks} фрагментами из {len(documents_to_seed)} документов.")

        # --- 3. Создаем задачи, соответствующие легенде чата ---
        print("📝 Создание демонстрационных задач...")
        
        now_aware = datetime.now().astimezone()

        tasks_to_create = [
            # Эта задача уже закрыта, как в сводке
            Task(id=13, title="Обновить SSL-сертификат на alpha-server", 
                 deadline=now_aware - timedelta(days=2), 
                 chat_id=DEMO_CHAT_ID, assignees="@daniil", is_completed=True),
            
            # Эта будет просрочена, как в сводке
            Task(id=14, title="Подготовить макеты для проекта 'Омега'", 
                 deadline=now_aware - timedelta(days=1), 
                 chat_id=DEMO_CHAT_ID, assignees="@maria", is_completed=False),

            Task(id=17, title="Финализировать макеты для инвесторов'", 
                 deadline=now_aware, 
                 chat_id=DEMO_CHAT_ID, assignees="@maria", is_completed=False),
        ]
        session.add_all(tasks_to_create)
        print(f"✅ Создано {len(tasks_to_create)} задачи с ID 13 и 14.")
        
        await session.commit()
        print("🎉 База данных успешно подготовлена для демонстрации!")

if __name__ == "__main__":
    print("ВАЖНО: Убедитесь, что ваши Docker-контейнеры (Postgres, MinIO) запущены.")
    print("Выполняется подключение к БД и наполнение данными...")
    
    # Простой и надежный запуск
    asyncio.run(seed_database())