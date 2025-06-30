# demo.Dockerfile

# Используем тот же базовый образ, что и для бота, для консистентности
FROM python:3.11-slim

# Устанавливаем рабочую директорию
WORKDIR /app

# Устанавливаем переменную окружения, чтобы Streamlit знал, где искать наш модуль
ENV PYTHONPATH=/app/src

# Копируем файл с зависимостями и устанавливаем их
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копируем весь контекст проекта (включая папку src и app.py)
COPY . .

# Открываем порт, на котором будет работать Streamlit
EXPOSE 8501

# Команда для запуска Streamlit-приложения
# --server.port 8501 - явно указываем порт
# --server.address 0.0.0.0 - позволяет подключаться к приложению извне контейнера
CMD ["streamlit", "run", "app.py", "--server.port", "8501", "--server.address", "0.0.0.0"]