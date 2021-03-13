"""12-factor settings."""
from pydantic import BaseSettings, HttpUrl, PostgresDsn, SecretStr, stricturl


class Settings(BaseSettings):
    """Application settings loaded from ENV variables.

    Reference:
        - [FastAPI uses Pydantic settings](https://fastapi.tiangolo.com/advanced/settings/#pydantic-settings)
        - [Pydantic custom types](https://pydantic-docs.helpmanual.io/usage/types/#pydantic-types)
        - [Pydantic URL types](https://pydantic-docs.helpmanual.io/usage/types/#urls)
    """

    environment: str = "development"
    elasticsearch_url: str = "localhost:9200"
    newsapi_key: str
    mediastack_key: str

    class Config:
        """Read settings from dotenv file."""

        env_file = ".env"
