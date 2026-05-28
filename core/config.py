from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    MONGO_URL: str
    DATABASE_NAME: str
    TOKEN:str
    JWT_SECRET:str
    WEBAPP_URL:str

    class Config:
        env_file = ".env"

settings = Settings()
