from pydantic import Field
from pydantic_settings import BaseSettings


class BemfaConfig(BaseSettings):
    BEMFA_URL: str = Field(default="bemfa.com")
    BEMFA_PORT: int = Field(default=8344)
    BEMFA_UID: str = Field(default="")
    BEMFA_TOPIC: str = Field(default="")
