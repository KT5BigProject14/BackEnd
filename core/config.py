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

# .env에 있는 [] 리스트 안에 있는 허용 cors 들을 사용할수 있게 분리하는 함수
def parse_cors(v: Any) -> list[str] | str:
    if isinstance(v, str) and not v.startswith("["):
        return [i.strip() for i in v.split(",")]
    elif isinstance(v, list | str):
        return v
    raise ValueError(v)

# .env의 값들의 형식을 정의
class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_ignore_empty=True, extra="ignore"
    )
    BACKEND_CORS_ORIGINS: Annotated[
        list[AnyUrl] | str, BeforeValidator(parse_cors)
    ] = []
    API_V1_STR: str = "/api/v1"
    SQLALCHEMY_DATABASE_URL: str
    PROJECT_NAME: str
    # SENTRY_DSN: Optional[str] = None
    ENVIRONMENT: str  # ENVIRONMENT 속성 추가
    ACCESS_TOKEN_EXPIRE_TIME: int
    REFRESH_TOKEN_EXPIRE_TIME: int
    ALGORITHM: str
    SECRET_KEY: str
    EMAIL_ADDR: str
    EMAIL_PW: str
    AWS_ACCESS_KEY: str
    AWS_SECRET_KEY: str
    REGIONE_NAME: str
    GOOGLE_CLIENT_ID : str
    GOOGLE_CLIENT_SECRET : str
    GOOGLE_REDIRECT_URI : str 
    NAVER_CLIENT_ID : str
    NAVER_CLIENT_SECRET : str
    NAVER_CALLBACK_URI : str
    LANGSERVE_URL: str

    # 보안적으로 중요한 설정값을 기본으로 두지 않게 하는 함수
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
