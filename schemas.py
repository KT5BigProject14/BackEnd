from pydantic import BaseModel, EmailStr, AnyHttpUrl
from pydantic_settings import BaseSettings
from typing import Optional, List, Union
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from jose import jwt, JWTError
from typing import List
from pydantic import Field


class UserBase(BaseModel):
    email: EmailStr
    password: str



class UserCreate(UserBase):
    user_name: str
    corporation: str
    business_number: int
    position: str
    phone: str


class User(BaseModel):
    email: EmailStr
    password: str


class JwtUser(BaseModel):
    email: EmailStr
    exp: str


class UserInfoBase(BaseModel):
    corporation: str
    business_number: int
    position: str
    phone: str
    user_name: str


class UserInfoCreate(UserInfoBase):
    pass


class UserInfo(UserInfoBase):
    class Config:
        from_attributes = True

# jwt encoder 추상 클래스


class AbstractEecoder(ABC):
    @abstractmethod
    def encode(
        self, data: dict, expires_delta: int, secret_key: str, algorithm: str
    ) -> str:
        pass

# jwt encoder 구현 클래스


class JWTEncoder(AbstractEecoder):
    def encode(
        self, data: dict, expires_delta: int, secret_key: str, algorithm: str
    ) -> str:
        to_encode = data.copy()
        expire = datetime.now(ZoneInfo("Asia/Seoul")) + \
            timedelta(minutes=expires_delta)
        to_encode.update({"exp": expire})
        return jwt.encode(to_encode, key=secret_key, algorithm=algorithm)

# jwt decoder 추상 클래스


class AbstractDecoder(ABC):
    @abstractmethod
    def decode(self, token: str, secret_key: str, algorithm: str) -> dict | None:
        pass

# jwt decoder 구현 클래스


class JWTDecoder(AbstractDecoder):
    def decode(
            self, token: str, secret_key: str, algorithm: str) -> dict | None:
        try:
            return jwt.decode(token, key=secret_key, algorithms=algorithm)
        except JWTError:
            return None


class SendEmail(BaseModel):
    email: EmailStr


class MessageOk(BaseModel):
    message: str = Field(default="OK")


class CheckEmail(SendEmail):
    is_active: bool | None


class CheckCode(SendEmail):
    verify_code: str


class Qna(BaseModel):
    email: EmailStr
    title: str
    content: str

    class Config:
        from_attributes = True
        
class CheckQna(Qna):
    qna_id : int
    
class Comment(BaseModel):
    qna_id : int
    content : str
    
class CheckComment(Comment):
    email: EmailStr
    comment_id: int

class ChangePassword(BaseModel):
    password: str
    new_password: str

class Settings(BaseSettings):
    PROJECT_NAME: str = "My FastAPI Project"
    API_V1_STR: str = "/api/v1"
    BACKEND_CORS_ORIGINS: Union[str, List[AnyHttpUrl]] = ["*"]

    class Config:
        case_sensitive = True
