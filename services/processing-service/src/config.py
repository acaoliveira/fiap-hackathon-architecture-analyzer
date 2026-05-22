from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    rabbitmq_url: str = "amqp://admin:admin@localhost:5672/"
    upload_service_url: str = "http://upload-service:8001"
    report_service_url: str = "http://report-service:8003"
    anthropic_api_key: str = ""
    storage_path: str = "/shared/uploads"
    claude_model: str = "claude-sonnet-4-6"
    claude_max_tokens: int = 8192
    max_retries: int = 3

    class Config:
        env_file = ".env"


settings = Settings()
