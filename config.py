from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    openai_api_key: str
    api_key: str

    class Config:
        env_file = ".env"