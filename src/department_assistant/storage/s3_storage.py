# src/department_assistant/storage/s3_storage.py
from minio import Minio
from ..core.config import settings
import logging

# Создаем клиент MinIO
minio_client = Minio(
    endpoint=f"{settings.minio_host}:{settings.minio_port}",
    access_key=settings.minio_user,
    secret_key=settings.minio_password,
    secure=settings.minio_secure
)

async def check_minio() -> bool:
    """Проверяет соединение с MinIO."""
    try:
        # Проверяем, существует ли какой-либо бакет (даже если нет, сам вызов пройдет успешно)
        minio_client.bucket_exists("healthcheck-bucket")
        logging.info("✅ MinIO connection successful.")
        return True
    except Exception as e:
        logging.error(f"❌ MinIO connection failed: {e}")
        return False