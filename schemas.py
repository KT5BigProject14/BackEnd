from pydantic import BaseModel, EmailStr
from typing import Optional


class UserBase(BaseModel):
    email: EmailStr


class UserCreate(UserBase):
    password: str


class User(UserBase):
    class Config:
        orm_mode = True


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
