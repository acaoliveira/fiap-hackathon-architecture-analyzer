from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    upload_service_url: str = "http://upload-service:8001"
    report_service_url: str = "http://report-service:8003"
    service_port: int = 8000

    class Config:
        env_file = ".env"


settings = Settings()
