from pydantic import BaseModel, EmailStr
from typing import Optional
from abc import ABC, abstractmethod
from datetime import datetime,timedelta
from zoneinfo import ZoneInfo
from jose import jwt, JWTError
from typing import List
from pydantic import Field
class UserBase(BaseModel):
    email: EmailStr


class UserCreate(UserBase):
    password: str


class User(UserBase):
    password: str



class UserInfoBase(BaseModel):
    email: EmailStr
    phone: Optional[str] = None
    corporation: Optional[str] = None
    business_number: Optional[int] = None


class UserInfoCreate(UserInfoBase):
    pass


class UserInfo(UserInfoBase):
    class Config:
        orm_mode = True

# jwt encoder 추상 클래스
class AbstaractEecoder(ABC):
    @abstractmethod
    def encode(
        self, data:dict, expires_delta: int , secret_key:str, algorithm: str
    ) -> str:
        pass

# jwt encoder 구현 클래스
class JWTEncoder(AbstaractEecoder):
    def encode(
        self, data:dict, expires_delta: int, secret_key:str, algorithm: str
    ) -> str:
        to_encode = data.copy()
        expire = datetime.now(ZoneInfo("Asia/Seoul")) + timedelta(minutes= expires_delta)
        to_encode.update({"exp":expire})
        return jwt.encode(to_encode,secret_key,algorithm=algorithm)

# jwt decoder 추상 클래스
class AbstaractDecoder(ABC):
    @abstractmethod
    def decode(self, token:str, secret_key:str, algorithm: str) -> dict | None:
        pass

# jwt decoder 구현 클래스
class JWTDecoder(AbstaractDecoder):
    def decode(
        self, token:str,secret_key:str, algorithm: str) -> dict | None:
        try:
            return jwt.decode(token, secret_key,algorithms=[algorithm])
        except JWTError:
            return None
            
class SendEmail(BaseModel):
    name: str
    email: EmailStr
    
class MessageOk(BaseModel):
    message: str = Field(default="OK")
    
class CheckEmail(SendEmail):
    is_active : bool | None
    
class CheckCode(SendEmail):
    verify_code : str