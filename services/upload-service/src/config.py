from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/upload_db"
    rabbitmq_url: str = "amqp://admin:admin@localhost:5672/"
    storage_path: str = "/shared/uploads"
    service_port: int = 8001
    max_file_size_bytes: int = 10 * 1024 * 1024  # 10 MB

    class Config:
        env_file = ".env"


settings = Settings()

ALLOWED_MIME_TYPES = frozenset(
    {
        "image/png",
        "image/jpeg",
        "image/webp",
        "image/gif",
        "application/pdf",
    }
)
