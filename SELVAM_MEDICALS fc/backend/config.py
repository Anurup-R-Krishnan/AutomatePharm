from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    APP_NAME: str = "Selvam Medicals"
    DATABASE_URL: str = "sqlite:///./selvam_medicals.db"
    REDIS_URL: str = "redis://localhost:6379"
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 480
    GST_NUMBER: str = ""
    DRUG_LICENSE: str = ""
    SHOP_NAME: str = "Selvam Medicals"
    SHOP_ADDRESS: str = ""
    SHOP_PHONE: str = ""
    TWILIO_SID: str = ""
    TWILIO_TOKEN: str = ""
    TWILIO_FROM: str = ""
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASS: str = ""

    class Config:
        env_file = ".env"

settings = Settings()
