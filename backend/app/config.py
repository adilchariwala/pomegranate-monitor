from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    mongodb_url: str
    database_name: str = "pomegranate_monitor"
    api_key: str
    debug: bool = False

    model_config = {"env_file": ".env"}


settings = Settings()
