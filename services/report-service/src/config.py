from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/report_db"
    rabbitmq_url: str = "amqp://admin:admin@localhost:5672/"
    service_port: int = 8003

    class Config:
        env_file = ".env"


settings = Settings()
