from core.config import settings
from api.main import api_router
from starlette.middleware.cors import CORSMiddleware
from fastapi.routing import APIRoute
import sentry_sdk
from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from models import Base, User as UserModel, UserInfo as UserInfoModel
from core.database import engine, get_db
from crud.login_crud import create_user_db, create_user_info_db, get_user, get_users, authenticate_user
from schemas import User, UserCreate, UserInfo, UserInfoCreate

# 데이터베이스 테이블 생성
Base.metadata.create_all(bind=engine)

# API 경로에 대해 고유 ID를 생성하는 사용자 정의 함수


def custom_generate_unique_id(route: APIRoute) -> str:
    return f"{route.tags[0]}-{route.name}"

# Sentry 설정 (필요시 활성화)
# if settings.SENTRY_DSN and settings.ENVIRONMENT != "local":
#     sentry_sdk.init(dsn=str(settings.SENTRY_DSN), enable_tracing=True)


# 애플리케이션 인스턴스를 생성
app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    generate_unique_id_function=custom_generate_unique_id,
)

# Set all CORS enabled origins
# 미들웨어를 추가하여 지정된 원본에서 오는 요청을 허용
if settings.BACKEND_CORS_ORIGINS:
    origins = settings.BACKEND_CORS_ORIGINS
    if isinstance(origins, str):
        origins = [origin.strip() for origin in origins.split(",")]

    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

# api_router를 애플리케이션에 포함하여 모든 API 엔드포인트를 등록
app.include_router(api_router, prefix=settings.API_V1_STR)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="localhost", port=8000)
