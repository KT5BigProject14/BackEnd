from schemas import JWTEncoder, JWTDecoder
from datetime import datetime
from zoneinfo import ZoneInfo
from fastapi import Request, Depends, HTTPException, status, Response
from fastapi.security.utils import get_authorization_scheme_param
from typing import Annotated
from core.database import get_db
from core.config import settings
from models import User
from sqlalchemy.orm import Session
from crud import login_crud
from fastapi.responses import JSONResponse

# JWT 클래스
class JWTService:
    # 각각의 변수 생성자로 초기화
    def __init__(self, enocder: JWTEncoder, decoder: JWTDecoder, algorithm: str, secret_key: str, access_token_expire_time: int, refresh_token_expire_time: int):
        self.encoder = enocder
        self.decoder = decoder
        self.algorithm = algorithm
        self.secret_key = secret_key
        self.access_token_expire_time = access_token_expire_time
        self.refresh_token_expire_time = refresh_token_expire_time
    # access_token 생성 메서드
    def create_access_token(self, data: dict) -> str:
        return self._create_token(data, self.access_token_expire_time)
    # refresh_token 생성 메서드
    def create_refresh_token(self, data: dict) -> str:
        return self._create_token(data, self.refresh_token_expire_time)
    # 토큰 생성 메서드
    def _create_token(self, data: dict, expires_delta: int) -> str:
        return self.encoder.encode(data, expires_delta, self.secret_key, self.algorithm)
    # 토큰 만료 기한 체크 메서드
    def check_token_expired(self, token: str) -> dict | None:
        payload = self.decoder.decode(token, self.secret_key, self.algorithm)
        now = datetime.timestamp(datetime.now(ZoneInfo("Asia/Seoul")))
        if payload and payload["exp"] < now:
            return None
        return payload

# JWT 인증 클래스
class JWTAuthentication:
    # JWT 생성자 초기화
    def __init__(self, jwt_service: JWTService):
        self.jwt_service = jwt_service

    # 유저 인증 메서드
    async def authenticate_user(
        self,
        request: Request,
        db: Session
    ) -> dict:
        # 헤더에서 Authorization 키로 들어오는 값 추출
        authorization = request.headers.get("Authorization")
        # Authorization 값이 있는경우
        if authorization:
            # bearer와 토큰 값을 분리
            scheme, token = get_authorization_scheme_param(authorization)
            # bearer가 있는 경우
            if scheme.lower() == "bearer":
                # 토큰을 만료 시간 체크하는 jwt_service 함수에 넣어서 만료시간이 지났는지 안지났는지 확인
                valid_payload = self.jwt_service.check_token_expired(token)
                # 만료시간이 안지나서 valid_payload가 있는경우
                if valid_payload:
                    # email, role type 값을 decoding한 토큰 값에서 가져옴
                    email = valid_payload.get("email")
                    role = valid_payload.get("role")
                    type = valid_payload.get('type')  # 'type'으로 변수명 변경
                    # role이 guest인경우
                    if role == "guest":
                        # 요청 주소가 유저 정보를 생성하는 url인 경우
                        if request.url.path == "/retriever/info/create/user":
                            # 유저 정보 조회
                            user = login_crud.get_user(db, email)
                            if user is None:
                                raise HTTPException(
                                    status_code=status.HTTP_401_UNAUTHORIZED,
                                    detail="Non-existent user.",
                                    headers={"WWW-Authenticate": "Bearer"},
                                )
                            # request.state에 조회한 user 정보를 넣고 user의 로그인 유형을 넣음
                            request.state.user = user
                            request.state.type = type
                            # 해당 정보를 return 하여 middleware에서 빠져나와 본 로직으로 들어감
                            return request.state.user
                        else:
                            # role이 guest이지만, 요청 주소가 유저 정보를 생성하는 주소가 아닌경우 unauthorized 에러 발생
                            raise HTTPException(
                                status_code=status.HTTP_401_UNAUTHORIZED,
                                detail="You are a guest user and cannot access this resource.",
                                headers={"WWW-Authenticate": "Bearer"},
                            )
                    # role이 guest가 아닌경우
                    # 유저 정보를 request.state에 넣어 return 하여 미들웨어를 빠져나옴
                    user = login_crud.get_user(db, email)
                    if user is None:
                        raise HTTPException(
                            status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="Non-existent user.",
                            headers={"WWW-Authenticate": "Bearer"},
                        )
                    request.state.user = user
                    request.state.type = type
                    return request.state.user
                # 토큰이 유효하지 않은 경우
                else:
                    # refresh_token을 쿠키에서 가져옴
                    refresh_token = request.cookies.get("refresh_token")
                    # 가져온 리프레쉬 토큰이 있는 경우
                    if refresh_token:
                        # 토큰이 만료됐는지 확인
                        refresh_payload = self.jwt_service.check_token_expired(refresh_token)
                        # 만약 만료되지 않았다면
                        if refresh_payload:
                            email = refresh_payload.get("email")
                            role = refresh_payload.get("role")
                            type = refresh_payload.get('type')
                            # refresh_token을 디코딩 하여 나온 정보를 통해 새로운 access_token을 발행
                            new_access_token = self.jwt_service.create_access_token({"email": email, "role": role, "type": type})
                            
                            # exception을 일으켜 프론트의 response 헤더에 새로운 access_token을 추가하여 전달
                            raise HTTPException(
                                status_code=status.HTTP_401_UNAUTHORIZED,
                                detail="Access token expired. New token issued.",
                                headers={
                                    "WWW-Authenticate": "Bearer",
                                    "new-access-token": new_access_token  # access_token이 만료되었을때 새롭게 발급된 토큰을 response header에 추가
                                }
                            )
                        # refresh_token도 만료된 경우 exception
                        else:
                            raise HTTPException(
                                status_code=status.HTTP_401_UNAUTHORIZED,
                                detail="Expired refresh token.",
                                headers={"WWW-Authenticate": "Bearer"},
                            )
                    # refresh_token이 없는 경우도 exception
                    else:
                        raise HTTPException(
                            status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="Expired or missing token.",
                            headers={"WWW-Authenticate": "Bearer"},
                        )
        # Authorization 이라는 키가 없는경우도 exception
        else:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Missing Authorization header.",
                headers={"WWW-Authenticate": "Bearer"},
            )




