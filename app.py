# app.py
import streamlit as st
import asyncio
from datetime import datetime

# --- Импорты ---
from src.department_assistant.services import llm_router, faq_service, task_service, llm_service
from src.department_assistant.core.models import Intent, TaskInfo, MeetingInfo

# --- Настройка страницы и асинхронного цикла ---
st.set_page_config(page_title="DepartmentAssistant Demo", page_icon="🤖", layout="wide")

if "event_loop" not in st.session_state:
    st.session_state.event_loop = asyncio.new_event_loop()
    asyncio.set_event_loop(st.session_state.event_loop)
loop = st.session_state.event_loop

# --- Константы и состояние ---
DEMO_CHAT_ID = -100123456789
if "history" not in st.session_state:
    st.session_state.history = [
        # --- Начало дня. Проблема ---
        {
            "role": "user",
            "name": "Анна (Менеджер)",
            "content": "Всем доброе утро! ☀️ Напоминаю, что сегодня в 10:00 у нас демо для инвесторов. @maria, как дела с макетами для презентации? Дедлайн был вчера, задача #14 горит красным."
        },
        {
            "role": "user",
            "name": "Мария (Дизайнер)",
            "content": "Анна, привет! Прошу прощения, вчера весь вечер не могла получить доступ к нашему S3 хранилищу, где лежат исходники. Какие там сейчас правила доступа?"
        },

        {
            "role": "bot",
            "content": "Согласно базе знаний, для доступа к S3-хранилищу 'omega-assets' теперь требуется обязательное подключение через корпоративный VPN 'Innovate-Secure'. (Источник: Регламент_Безопасности.pdf)"
        },
        {
            "role": "user",
            "name": "Мария (Дизайнер)",
            "content": "А, точно! Тогда я сейчас быстро все доделаю. К 12 часам макеты будут готовы."
        },

        # --- Демонстрация создания задачи и интерактивности ---
        {
            "role": "bot_proposal",
            "type": "task",
            "content": 'Создать задачу "Финализировать макеты для инвесторов"?\n<b>Дедлайн:</b> сегодня в 12:00\n<b>Ответственные:</b> @maria',
            "id": "prop_hist_1"
        },
        # Это сообщение имитирует то, что появится ПОСЛЕ того, как пользователь нажмет "Подтвердить"
        # Для начального отображения его можно закомментировать, но для полноты истории оно здесь
        {
            "role": "bot",
            "content": "✅ Задача #17: \"Финализировать макеты для инвесторов\" создана. Мария подтвердила."
        },

        # --- Демонстрация создания встречи ---
        {
            "role": "user",
            "name": "Анна (Менеджер)",
            "content": "Отлично! Тогда давайте проведем ревью макетов сразу после этого. Предлагаю созвон сегодня в 12:30."
        },
        {
            "role": "bot_proposal",
            "type": "meeting",
            "content": 'Создать встречу "Ревью макетов для инвесторов" сегодня в 12:30–13:30?',
            "id": "prop_hist_2"
        },
        {
            "role": "bot",
            "content": "✅ Встреча \"Ревью макетов для инвесторов\" создана. Анна подтвердила."
        },

        # --- Итоговая сводка дня (идет последней) ---
        {
            "role": "bot_summary",
            "content": """
            📝 **Сводка за сегодняшний день (30.06.2025):**
            - **Ключевые события:**
                - Решена проблема с доступом к S3 благодаря базе знаний ассистента.
                - Назначена новая встреча "Ревью макетов для инвесторов" на 12:30.
            - **Задачи:**
                - 🆕 Создана задача #17: 'Финализировать макеты для инвесторов' для @maria с дедлайном сегодня.
            - **Обсуждения:**
                - Главная тема: срочная подготовка к демо для инвесторов.
            """
        },
    ]
    
if "prompt_to_run" not in st.session_state:
    st.session_state.prompt_to_run = None

if 'show_welcome' not in st.session_state:
    st.session_state.show_welcome = True


if st.session_state.show_welcome:
    # Используем st.container() чтобы визуально сгруппировать элементы
    with st.container():
        st.header("Добро пожаловать в демо-версию DepartmentAssistant! 👋")
        st.markdown("""
            ### Легенда
            Вы — новый сотрудник в компании **"Innovate Forward Inc."** и вас добавили в 
            основной рабочий чат проекта "Омега". В чате уже кипит работа: ставятся задачи, 
            обсуждаются вопросы, планируются встречи. Команде помогает 
            `DepartmentAssistant`, который анализирует каждое сообщение.
            
            **Ваша задача** — освоиться и попробовать повзаимодействовать с ассистентом, 
            используя примеры из меню слева или свои собственные фразы.
        """)
        st.success("Все ваши действия (создание задач и т.д.) будут сохранены в базу данных.")
        
        # Кнопка, которая скроет это сообщение
        if st.button("Начать работу!", type="primary"):
            st.session_state.show_welcome = False
            st.rerun() # Перезагружаем страницу, чтобы скрыть блок
    
    # Добавляем разделитель и останавливаем выполнение остальной части скрипта
    st.markdown("---")
    st.stop()

# --- Сайдбар с интерактивными примерами ---
with st.sidebar:
    st.title("Меню Ассистента")
    st.info("Кликните на пример, чтобы запустить его.")

    def set_prompt_to_run(text):
        st.session_state.prompt_to_run = text

    st.subheader("❓ База знаний", divider="blue")
    if st.button("Как оформить отпуск?", use_container_width=True): set_prompt_to_run("Как оформить отпуск?")
    if st.button("Какой у нас стандартный ноутбук?", use_container_width=True): set_prompt_to_run("Какой у нас стандартный ноутбук?")

    st.subheader("✔️ Управление задачами", divider="green")
    if st.button("Создать: 'Развернуть новую версию'", use_container_width=True): set_prompt_to_run("Нужно развернуть новую версию на stage до конца дня @daniil")
    if st.button("Показать активные задачи", use_container_width=True): set_prompt_to_run("/tasks")
    if st.button("Закрыть задачу #14", use_container_width=True): set_prompt_to_run("/close 14")

    st.subheader("📅 Управление встречами (время МСК)", divider="orange")
    if st.button("Создать: 'Синк по результатам недели'", use_container_width=True): set_prompt_to_run("давайте созвонимся в пятницу в 16:00 на синк по результатам недели")

    st.divider() # Горизонтальная черта для разделения

    st.subheader("💡 О проекте", anchor=False)

    st.markdown(
        """
        Это **технологическая демонстрация (Proof of Concept)**, показывающая 
        ключевые возможности корпоративного ИИ-ассистента.
        """
    )

    st.info(
        """
        **Основная идея** — интеграция ассистента в ваш рабочий чат **Telegram**, 
        где он будет автоматизировать рутину и помогать команде.
        
        Мы также открыты к обсуждению интеграции с другими платформами (Bitrix, Notion, Google Calendar...).
        """, 
        icon="🚀"
    )
    
    st.caption("v0.1.0-demo")

# --- Основной UI чата ---
st.header("💬 Рабочий чат: #general")

async def process_user_input(user_input: str):
    st.session_state.history.append({"role": "user", "name": "Вы", "content": user_input})
    with st.chat_message("assistant", avatar="🤖"):
        with st.spinner("Анализирую..."):
            # ... (Код process_user_input остается таким же, как в предыдущей полной версии)
            # Я скопирую его сюда для полноты.
            response_text, is_html = "", False
            if user_input.startswith('/tasks'):
                tasks = await task_service.get_active_tasks_for_chat(DEMO_CHAT_ID)
                if not tasks: response_text = "🎉 Все задачи выполнены!"
                else:
                    lines = ["<b>📝 Активные задачи:</b>"]
                    for task in tasks:
                        deadline_dt = task.deadline.astimezone(datetime.now().astimezone().tzinfo) if task.deadline else None
                        is_overdue = deadline_dt and deadline_dt < datetime.now().astimezone()
                        deadline_str = f" (до {deadline_dt.strftime('%d.%m.%Y')}){'❗️' if is_overdue else ''}" if deadline_dt else ""
                        assignees_str = f" {task.assignees}" if task.assignees else ""
                        lines.append(f"\n• <code>#{task.id}</code>: {task.title}{assignees_str}{deadline_str}")
                    response_text, is_html = "\n".join(lines), True
            elif user_input.startswith('/close'):
                try:
                    task_id = int(user_input.split()[1])
                    closed_task = await task_service.close_task(task_id, DEMO_CHAT_ID)
                    response_text, is_html = (f"✅ Задача <code>#{task_id}</code>: \"{closed_task.title}\" закрыта." if closed_task else f"Не удалось найти активную задачу с ID <code>#{task_id}</code>."), True
                except (IndexError, ValueError): response_text = "Пожалуйста, укажите корректный ID. Пример: `/close 14`"
            else:
                intent = await llm_router.classify_intent(user_input)
                if intent == Intent.FAQ_QUESTION:
                    context = await faq_service.find_similar_faq(user_input)
                    response_text = await llm_service.generate_answer_from_context(user_input, context)
                elif intent in [Intent.TASK_CREATION, Intent.MEETING_CREATION]:
                    prop_type = "task" if intent == Intent.TASK_CREATION else "meeting"
                    info = await (llm_router.extract_task_info if prop_type == "task" else llm_router.extract_meeting_info)(user_input)
                    if info:
                        st.session_state[f'proposed_{prop_type}'] = info
                        content = ""
                        if isinstance(info, TaskInfo):
                            lines = [f'Cоздать задачу "{info.title}"?']
                            if info.deadline_str: lines.append(f"<b>Дедлайн:</b> {info.deadline_str}")
                            if info.assignees: lines.append(f"<b>Ответственные:</b> {' '.join(info.assignees)}")
                            content = "\n".join(lines)
                        elif isinstance(info, MeetingInfo):
                            start_str, end_str = info.start_time.strftime('%d.%m.%Y %H:%M'), info.end_time.strftime('%H:%M')
                            content = f"Создать встречу \"{info.title}\" на {start_str}–{end_str}?"
                        st.session_state.history.append({"role": "bot_proposal", "type": prop_type, "content": content, "id": f"prop_{len(st.session_state.history)}"})
                        return
                else: return
            st.session_state.history.append({"role": "bot", "content": response_text, "html": is_html})

for i, msg in enumerate(st.session_state.history):
    #avatar = "🧑‍💻" if msg.get("name") not in [None, "Вы"] else "😎" if msg.get("name") == "Вы" else "🤖"
    role = "user" if msg["role"] == "user" else "assistant"
    with st.chat_message(role):
        if msg["role"] == "user":
            st.write(f"**{msg['name']}**")
            # ФИКС 1: Отображаем контент сообщения пользователя
            st.write(msg["content"])
        elif msg["role"] == "bot_summary":
            st.info(msg["content"], icon="ℹ️")
        elif msg["role"] == "bot_proposal":
            st.write(msg["content"], unsafe_allow_html=True)
            prop_id = msg["id"]
            col1, col2, _ = st.columns([1.5, 1, 5])
            if col1.button("✅ Подтвердить", key=f"confirm_{prop_id}", use_container_width=True):
                if msg["type"] == "task":
                    info = st.session_state.get('proposed_task')
                    if info:
                        created_task = loop.run_until_complete(task_service.create_task(info, DEMO_CHAT_ID, None))
                        # УЛУЧШЕНИЕ 3: Заменяем предложение на результат
                        msg["role"] = "bot"
                        msg["content"] = f"✅ Задача #{created_task.id}: \"{created_task.title}\" создана. Вы подтвердили."
                        if 'proposed_task' in st.session_state: del st.session_state['proposed_task']
                else: # meeting
                    info = st.session_state.get('proposed_meeting')
                    if info:
                        msg["role"] = "bot"
                        msg["content"] = f"✅ Встреча \"{info.title}\" запланирована. Вы подтвердили."
                        if 'proposed_meeting' in st.session_state: del st.session_state['proposed_meeting']
                st.rerun()
            if col2.button("❌ Отмена", key=f"cancel_{prop_id}", use_container_width=True):
                # УЛУЧШЕНИЕ 3: Заменяем предложение на результат
                msg["role"] = "bot"
                msg["content"] = "Действие отменено."
                st.rerun()
        else: # role == "bot"
            st.write(msg["content"], unsafe_allow_html=msg.get("html", False))

# --- Поле ввода и обработка действий ---
# ФИКС 2: Логика для интерактивного сайдбара
if st.session_state.prompt_to_run:
    user_input = st.session_state.prompt_to_run
    st.session_state.prompt_to_run = None # Очищаем, чтобы не запускалось повторно
    loop.run_until_complete(process_user_input(user_input))
    st.rerun()
else:
    user_input = st.chat_input("Спросите что-нибудь, создайте задачу или встречу...")
    if user_input:
        loop.run_until_complete(process_user_input(user_input))
        st.rerun()