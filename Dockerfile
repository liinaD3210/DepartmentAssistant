# Dockerfile
FROM python:3.11-slim

WORKDIR /app

ENV PYTHONPATH=/app/src

# Копируем и устанавливаем зависимости
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копируем исходный код
COPY . .

# Команда для запуска бота
CMD ["python", "-m", "department_assistant"]