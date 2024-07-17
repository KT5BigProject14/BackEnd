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


class JWTService:
    def __init__(self, enocder: JWTEncoder, decoder: JWTDecoder, algorithm: str, secret_key: str, access_token_expire_time: int, refresh_token_expire_time: int):
        self.encoder = enocder
        self.decoder = decoder
        self.algorithm = algorithm
        self.secret_key = secret_key
        self.access_token_expire_time = access_token_expire_time
        self.refresh_token_expire_time = refresh_token_expire_time

    def create_access_token(self, data: dict) -> str:
        return self._create_token(data, self.access_token_expire_time)

    def create_refresh_token(self, data: dict) -> str:
        return self._create_token(data, self.refresh_token_expire_time)

    def _create_token(self, data: dict, expires_delta: int) -> str:
        return self.encoder.encode(data, expires_delta, self.secret_key, self.algorithm)

    def check_token_expired(self, token: str) -> dict | None:
        payload = self.decoder.decode(token, self.secret_key, self.algorithm)
        now = datetime.timestamp(datetime.now(ZoneInfo("Asia/Seoul")))
        if payload and payload["exp"] < now:
            return None
        return payload

class JWTAuthentication:
    def __init__(self, jwt_service: JWTService):
        self.jwt_service = jwt_service

    async def authenticate_user(
        self,
        request: Request,
        response: Response,
        db: Session
    ) -> dict:
        authorization = request.headers.get("Authorization")
        if authorization:
            scheme, token = get_authorization_scheme_param(authorization)
            if scheme.lower() == "bearer":
                valid_payload = self.jwt_service.check_token_expired(token)
                if valid_payload:
                    email = valid_payload.get("email")
                    role = valid_payload.get("role")
                    type = valid_payload.get('type')  # 'type'으로 변수명 변경

                    if role == "guest":
                        # Check if the current endpoint is '/retriever/info/create/user'
                        if request.url.path == "/retriever/info/create/user":
                            user = login_crud.get_user(db, email)
                            if user is None:
                                raise HTTPException(
                                    status_code=status.HTTP_401_UNAUTHORIZED,
                                    detail="Non-existent user.",
                                    headers={"WWW-Authenticate": "Bearer"},
                                )
                            # Set request.state.user to the token's payload dictionary
                            request.state.user = user
                            request.state.type = type
                            return request.state.user
                        else:
                            raise HTTPException(
                                status_code=status.HTTP_401_UNAUTHORIZED,
                                detail="You are a guest user and cannot access this resource.",
                                headers={"WWW-Authenticate": "Bearer"},
                            )

                    user = login_crud.get_user(db, email)
                    if user is None:
                        raise HTTPException(
                            status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="Non-existent user.",
                            headers={"WWW-Authenticate": "Bearer"},
                        )
                    # Set request.state.user to the token's payload dictionary
                    request.state.user = user
                    request.state.type = type
                    return request.state.user
                else:
                    refresh_token = request.cookies.get("refresh_token")
                    if refresh_token:
                        refresh_payload = self.jwt_service.check_token_expired(refresh_token)
                        if refresh_payload:
                            email = refresh_payload.get("email")
                            role = refresh_payload.get("role")
                            type = refresh_payload.get('type')
                            new_access_token = self.jwt_service.create_access_token({"email": email, "role": role, "type": type})
                            raise HTTPException(
                                status_code=status.HTTP_401_UNAUTHORIZED,
                                detail="Access token expired. New token issued.",
                                headers={"WWW-Authenticate": f"Bearer {new_access_token}"},
                            )
                        else:
                            raise HTTPException(
                                status_code=status.HTTP_401_UNAUTHORIZED,
                                detail="Expired refresh token.",
                                headers={"WWW-Authenticate": "Bearer"},
                            )
                    else:
                        raise HTTPException(
                            status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="Expired or missing token.",
                            headers={"WWW-Authenticate": "Bearer"},
                        )
        else:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Missing Authorization header.",
                headers={"WWW-Authenticate": "Bearer"},
            )


