from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    SQLALCHEMY_DATABASE_URL: str = "mysql+pymysql://root:aivle@localhost:3306/retriever"

    class Config:
        env_file = ".env"

settings = Settings()
