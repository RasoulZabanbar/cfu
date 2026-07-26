from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache

class Env_Config(BaseSettings):
    database_url: str
    storage_dir: str = "/data/licenses" 
    bale_bot_token: str
    bale_webhook_url: str 
    bale_api_base: str
    bale_bot_id: str
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache
def get_env_setup():
    return Env_Config()
