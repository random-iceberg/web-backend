from pydantic import BaseSettings

class Settings(BaseSettings):
    model_api_url: str = "http://model:8000/inference"

settings = Settings()
