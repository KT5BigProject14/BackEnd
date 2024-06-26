from pydantic_settings import BaseSettings, SettingsConfigDict
import warnings
from typing import Optional
from typing import Annotated, Any, Literal
from pydantic import (
    AnyUrl,
    BeforeValidator,
    HttpUrl,
    PostgresDsn,
    computed_field,
    model_validator,
)

def parse_cors(v: Any) -> list[str] | str:
    if isinstance(v, str) and not v.startswith("["):
        return [i.strip() for i in v.split(",")]
    elif isinstance(v, list | str):
        return v
    raise ValueError(v)

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_ignore_empty=True, extra="ignore"
    )
    BACKEND_CORS_ORIGINS: Annotated[
        list[AnyUrl] | str, BeforeValidator(parse_cors)
    ] = []
    API_V1_STR: str = "/api/v1"
    SQLALCHEMY_DATABASE_URL: str = "mysql+pymysql://root:aivle@localhost:3306/retriever"
    PROJECT_NAME: str
    # SENTRY_DSN: Optional[str] = None
    ENVIRONMENT: str  # ENVIRONMENT 속성 추가

    def _check_default_secret(self, var_name: str, value: str | None) -> None:
        if value == "changethis":
            message = (
                f'The value of {var_name} is "changethis", '
                "for security, please change it, at least for deployments."
            )
            if self.ENVIRONMENT == "local":
                warnings.warn(message, stacklevel=1)
            else:
                raise ValueError(message)    

settings = Settings()
