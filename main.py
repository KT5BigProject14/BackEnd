from core.config import settings
from api.main import api_router
from starlette.middleware.cors import CORSMiddleware
from fastapi.routing import APIRoute
import sentry_sdk
from fastapi import FastAPI, Depends, HTTPException, status
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
import logging
# 데이터베이스 테이블 생성
Base.metadata.create_all(bind=engine)

# API 경로에 대해 고유 ID를 생성하는 사용자 정의 함수


def custom_generate_unique_id(route: APIRoute) -> str:
    return f"{route.tags[0]}-{route.name}"

# Sentry 설정 (필요시 활성화)
# if settings.SENTRY_DSN and settings.ENVIRONMENT != "local":
#     sentry_sdk.init(dsn=str(settings.SENTRY_DSN), enable_tracing=True)
logging.basicConfig(level=logging.DEBUG,  # 로그 레벨을 DEBUG로 설정
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

logger = logging.getLogger(__name__)

# 애플리케이션 인스턴스를 생성
app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    generate_unique_id_function=custom_generate_unique_id,
)

# deps에서 정의한 JWT
jwt_service = JWTService(JWTEncoder(), JWTDecoder(), settings.ALGORITHM, settings.SECRET_KEY,
                         settings.ACCESS_TOKEN_EXPIRE_TIME, settings.REFRESH_TOKEN_EXPIRE_TIME)

# 위에서 만든 JWT를 주입받은 jwt 인증 객체
jwt_authentication = JWTAuthentication(jwt_service)

# jwt 인증을 위한 미들웨어
@app.middleware("http")
async def jwt_middleware(request: Request, call_next):
    # 아래 url로 오는 요청은 pass(로그인 요청 등)
    if (
        request.url.path.startswith("/docs") or
        request.url.path.startswith("/retriever/user") or
        request.url.path.startswith("/retriever/openapi.json") or
        request.url.path.startswith("/retriever/user/login/oauth2/code")
    ):
        response = await call_next(request)
        return response

    # 예외 처리 대신 기본적으로 인증을 시도합니다.
    try:
        db = next(get_db())
        # 인증을 완료하고 return 된 값 user  변수에 추가
        user = await jwt_authentication.authenticate_user(request, db)
        # user 가 있는 경우 
        if user:
            # user를 request.state.user에 넣음
            request.state.user = user
            # 다음 단계로 진행
            response = await call_next(request)
        else:
            # 없는 경우 에러
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Only admin users are allowed to access this resource.",
                headers={"WWW-Authenticate": "Bearer"},
            )
    except HTTPException as e:
        response = JSONResponse(status_code=e.status_code, content={"detail": e.detail})
        if 'new-access-token' in e.headers:
            response.headers['new-access-token'] = e.headers['new-access-token']

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
        expose_headers=["new-access-token"] # 여기에 헤더를 추가합니다
    )
#  클라이언트의 요청에 세션 쿠키를 추가하고, 서버 측에서 이 세션 데이터를 해독하여 사용하여 HTTP 요청 간에 사용자 데이터를 유지
app.add_middleware(SessionMiddleware,secret_key=settings.SECRET_KEY)
# api_router를 애플리케이션에 포함하여 모든 API 엔드포인트를 등록
app.include_router(api_router, prefix=settings.API_V1_STR)
