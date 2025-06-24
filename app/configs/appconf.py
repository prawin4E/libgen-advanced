from pydantic_settings import BaseSettings, SettingsConfigDict

class Environmentals(BaseSettings):
    MODEL_HAIKU: str

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

env = Environmentals()