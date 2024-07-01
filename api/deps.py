from schemas import JWTEncoder, JWTDecoder
from datetime import datetime,timedelta
from zoneinfo import ZoneInfo
from fastapi import Request, Depends, HTTPException, status
from fastapi.security.utils import get_authorization_scheme_param
from typing import Annotated

from core.config import settings  # settings 모듈을 core.config에서 불러옴
from models import User  # User 모델을 import

from sqlalchemy.orm import Session
from crud import login_crud  # user_repository 모듈을 import

class JWTService:
    def __init__(
        self,
        enocder: JWTEncoder,
        decoder: JWTDecoder,
        algorithm: str = None,
        secret_key: str = None,
        access_token_expire_time: int = None,
        refresh_token_expire_time: int = None,
    ):
        self.encoder = enocder
        self.decoder = decoder
        self.algorithm = algorithm
        self.secret_key = secret_key
        self.access_token_expire_time = access_token_expire_time
        self.refresh_token_expire_time = refresh_token_expire_time
        
    def create_access_token(self, data:dict) -> str:
        return self._create_token(data,self.access_token_expire_time)
    
    def create_refresh_token(self, data:dict) ->str:
        return self._create_token(data,self.refresh_token_expire_time)
    
    def _create_token(self,data:dict, expires_delta: int) -> str:
        return self.encoder.encode(data,expires_delta,self.secret_key,self.algorithm)
    
    def check_token_expired(self, token:str) -> dict | None:
        payload = self.decoder.decode(token, self.secret_key, self.algorithm)
        
        now = datetime.timestamp(datetime.now(ZoneInfo("Asia/Seoul")))
        if payload and payload["exp"] < now:
            return None
        
        return payload

'''
아래 부분 부터는 나중에 middle ware로 빼서 요청마다 authentificate 한지 판별
'''
    
async def validate_token(request: Request) -> str | None:
    authorization = request.headers.get("Authorization")
    scheme, param = get_authorization_scheme_param(authorization)
    if not authorization or scheme.lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token is invalid",
            headers={"WWW-Authenticate": "Bearer"},
            code="INVALID_TOKEN",
        )
    return param
 
class JWTAuthentication:
    async def __call__(
        self,
        db: Session,
        token: Annotated[str, Depends(validate_token)],
    ):
        try:
            valid_payload = JWTService.check_token_expired(token)
            if valid_payload:
                email = valid_payload.get("email")
            else:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Expired or changed token.",
                    headers={"WWW-Authenticate": "Bearer"},
                    code="EXPIRED_TOKEN",
                )
        except HTTPException as e:
            raise e
        else:
            user = await login_crud.get_user(db, email)
            if user is None:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Non-existent user",
                    headers={"WWW-Authenticate": "Bearer"},
                    code="INVALID_USER",
                )
            else:
                return user
 
get_current_user = JWTAuthentication()
GetCurrentUser = Annotated[User, Depends(get_current_user)]