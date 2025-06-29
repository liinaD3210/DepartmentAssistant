# app.py
import streamlit as st
import asyncio
from datetime import datetime, timedelta
import time

# --- Настройка страницы (должна быть первым вызовом Streamlit) ---
st.set_page_config(
    page_title="DepartmentAssistant Demo",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
)

# --- Импорты нашей бизнес-логики ---
# Помещаем их после настройки страницы, чтобы избежать потенциальных проблем
from src.department_assistant.services import llm_router, faq_service, task_service
from src.department_assistant.core.models import Intent, TaskInfo, MeetingInfo

# --- Константы и хелперы ---
DEMO_CHAT_ID = -100123456789  # Фиктивный ID для нашего демо-чата

# --- Инициализация состояния чата в Streamlit ---
if "history" not in st.session_state:
    # Предзаполняем историю чата для демонстрации
    st.session_state.history = [
        {"role": "bot_summary", "content": "📝 **Сводка за 22.06.2025:**\n- Обсуждали запуск проекта 'Омега'.\n- Создана задача #14 'Подготовить макеты для 'Омега''.\n- Назначена встреча на сегодня для обсуждения рисков."},
        {"role": "user", "name": "Анна", "content": "Коллеги, нужно срочно подготовить презентацию для инвесторов к среде!"},
        {"role": "bot", "content": "✅ Задача \"Подготовить презентацию для инвесторов\" создана (ID: 15)."},
        {"role": "user", "name": "Даниил", "content": "как мне взять отпуск?"},
        {"role": "bot", "content": "Я нашел следующую информацию: для оформления ежегодного оплачиваемого отпуска сотрудник должен подать заявление не позднее, чем за 14 календарных дней до предполагаемой даты начала отпуска. Заявление подается через корпоративный портал 'MyAlpha'."}
    ]
if "user_input" not in st.session_state:
    st.session_state.user_input = ""


# --- Боковая панель (Sidebar) ---
with st.sidebar:
    st.title("🤖 DepartmentAssistant")
    st.info(
        "Это интерактивная демонстрация корпоративного ИИ-ассистента. "
        "Попробуйте разные сценарии в чате справа."
    )
    
    with st.expander("❓ Задать вопрос по базе знаний"):
        st.code("как оформить отпуск?")
        st.code("какой у нас стандартный ноутбук?")
        st.code("как часто менять пароль?")

    with st.expander("✔️ Создать задачу"):
        st.code("нужно составить смету до конца недели @daniil")
        st.code("заказать пиццу в офис на 19:00")

    with st.expander("📅 Назначить встречу"):
        st.code("давайте созвонимся завтра в 11 обсудить маркетинг")

    with st.expander("⚙️ Управлять задачами"):
        st.code("/tasks")
        st.code("/close 15")

    st.success("Все созданные задачи и встречи сохраняются в реальной базе данных!")

# --- Основной интерфейс ---
st.header("Рабочий чат команды #general")

# --- Главная асинхронная функция-обработчик ---
async def process_user_input(user_input: str):
    st.session_state.history.append({"role": "user", "name": "Вы", "content": user_input})

    # Эффект "печатает..."
    with st.chat_message("assistant", avatar="🤖"):
        with st.spinner("Думаю..."):
            # Команды
            if user_input.startswith('/tasks'):
                tasks = await task_service.get_active_tasks_for_chat(DEMO_CHAT_ID)
                if not tasks:
                    response_text = "🎉 Все задачи выполнены! Отличная работа!"
                else:
                    response_lines = ["<b>📝 Активные задачи:</b>"]
                    for task in tasks:
                        deadline_str = f" (до {task.deadline.strftime('%d.%m.%Y')})" if task.deadline else ""
                        assignees_str = f" {task.assignees}" if task.assignees else ""
                        response_lines.append(f"• <code>#{task.id}</code>: {task.title}{assignees_str}{deadline_str}")
                    response_text = "\n".join(response_lines)
                st.session_state.history.append({"role": "bot", "content": response_text, "html": True})

            elif user_input.startswith('/close'):
                try:
                    task_id = int(user_input.split()[1])
                    closed_task = await task_service.close_task(task_id, DEMO_CHAT_ID)
                    if closed_task:
                        response_text = f"✅ Задача <code>#{task_id}</code>: \"{closed_task.title}\" закрыта."
                    else:
                        response_text = f"Не удалось найти активную задачу с ID <code>#{task_id}</code>."
                    st.session_state.history.append({"role": "bot", "content": response_text, "html": True})
                except (IndexError, ValueError):
                    st.session_state.history.append({"role": "bot", "content": "Пожалуйста, укажите корректный ID задачи. Пример: `/close 14`"})
            
            # LLM-роутер
            else:
                intent = await llm_router.classify_intent(user_input)
                if intent == Intent.FAQ_QUESTION:
                    context = await faq_service.find_similar_faq(user_input)
                    answer = await faq_service.generate_answer_from_context(user_input, context)
                    st.session_state.history.append({"role": "bot", "content": answer})
                # TODO: Добавить обработку других интентов, если нужно. Пока для демо этого достаточно.
                else:
                    st.session_state.history.append({"role": "bot", "content": "Я пока не умею обрабатывать такие запросы в этой демо-версии, но я понял, что вы хотите. 😊"})


# --- Отображение истории чата ---
for msg in st.session_state.history:
    if msg["role"] == "user":
        with st.chat_message("user", avatar="🧑‍💻"):
            st.write(f"**{msg['name']}**")
            st.write(msg["content"])
    elif msg["role"] == "bot_summary":
        st.info(msg["content"], icon="ℹ️")
    elif msg["role"] == "bot":
        with st.chat_message("assistant", avatar="🤖"):
            st.write(msg["content"], unsafe_allow_html=msg.get("html", False))

# --- Поле ввода ---
# Эта логика исправляет ошибку
user_input = st.chat_input("Спросите что-нибудь у ассистента...")
if user_input:
    asyncio.run(process_user_input(user_input))
    # Перезагружаем страницу, чтобы отобразить ответ
    st.rerun()