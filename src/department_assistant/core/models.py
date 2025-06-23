# src/department_assistant/core/models.py
from enum import Enum
from datetime import datetime
from pydantic import BaseModel, Field

class Intent(str, Enum):
    """Категории (намерения) пользователя, которые определяет LLM-роутер."""
    FAQ_QUESTION = "faq_question"
    TASK_CREATION = "task_creation"
    MEETING_CREATION = "meeting_creation"
    IRRELEVANT = "irrelevant"

    # Это позволит нам легко проверить, является ли строка валидной категорией
    @classmethod
    def _missing_(cls, value):
        return cls.IRRELEVANT
    
class MeetingInfo(BaseModel):
    """Информация о встрече, извлеченная из текста."""
    title: str = "Созвон" # Тема по умолчанию
    start_time: datetime
    # Добавим пока что длительность по умолчанию 1 час
    end_time: datetime | None = None