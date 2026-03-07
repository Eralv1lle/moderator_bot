from pydantic_settings import BaseSettings, SettingsConfigDict


class Config(BaseSettings):
    BOT_TOKEN: str
    TEXT_MODEL: str
    IMAGE_MODEL: str
    GROUP_ID: int
    ADMIN_ID: int
    DURATION_MINUTES: int

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )


config = Config() # type: ignore