from pydantic_settings import SettingsConfigDict

from config.bemfa_config import BemfaConfig


class SmartDeviceConfig(BemfaConfig):
    model_config = SettingsConfigDict(
        # read from dotenv format config file
        env_file=".env",
        env_file_encoding="utf-8",
        # ignore extra attributes
        extra="ignore",
    )
