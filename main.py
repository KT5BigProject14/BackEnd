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
from starlette.middleware.sessions import SessionMiddleware
from fastapi import FastAPI, Request, Response, Depends
from api.deps import JWTService, JWTAuthentication, get_db
from schemas import JWTEncoder, JWTDecoder
from fastapi.responses import JSONResponse
from core.config import settings
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

jwt_service = JWTService(JWTEncoder(), JWTDecoder(), settings.ALGORITHM, settings.SECRET_KEY,
                         settings.ACCESS_TOKEN_EXPIRE_TIME, settings.REFRESH_TOKEN_EXPIRE_TIME)
jwt_authentication = JWTAuthentication(jwt_service)

@app.middleware("http")
async def jwt_middleware(request: Request, call_next):
    if request.url.path.startswith("/docs") or request.url.path.startswith("/retriever/users/") or request.url.path.startswith("/retriever/openapi.json") or request.url.path.startswith("/token"):   # "/public" 경로는 미들웨어 적용 제외
        response = await call_next(request)
        return response
    response = Response("Internal server error", status_code=500)
    try:
        db = next(get_db())
        await jwt_authentication.authenticate_user(request, response, db)
        response = await call_next(request)
        request.state.user = request.state.user
    except HTTPException as e:
        response = JSONResponse(status_code=e.status_code, content={"detail": e.detail})
    return response
# # Set all CORS enabled origins
# 미들웨어를 추가하여 지정된 원본에서 오는 요청을 허용
if settings.BACKEND_CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            str(origin).strip("/") for origin in settings.BACKEND_CORS_ORIGINS
        ],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
#  클라이언트의 요청에 세션 쿠키를 추가하고, 서버 측에서 이 세션 데이터를 해독하여 사용하여 HTTP 요청 간에 사용자 데이터를 유지
app.add_middleware(SessionMiddleware,secret_key=settings.SECRET_KEY)
# api_router를 애플리케이션에 포함하여 모든 API 엔드포인트를 등록
app.include_router(api_router, prefix=settings.API_V1_STR)
