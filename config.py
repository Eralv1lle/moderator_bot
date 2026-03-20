from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator
from typing import List


class Config(BaseSettings):
    BOT_TOKEN: str
    TEXT_MODEL: str
    IMAGE_MODEL: str
    GROUP_IDS: List[int]
    ADMIN_IDS: List[int]
    DURATION_MINUTES: int

    @field_validator('GROUP_IDS', 'ADMIN_IDS', mode='before')
    @classmethod
    def parse_ids(cls, v):
        if isinstance(v, str):
            return [int(x.strip()) for x in v.split(',')]
        return v

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )


config = Config()  # type: ignore