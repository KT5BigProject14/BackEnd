from pydantic import BaseModel, EmailStr
from typing import Optional


class UserBase(BaseModel):
    user_id: str


class UserCreate(UserBase):
    password: str


class User(UserBase):
    class Config:
        orm_mode = True


class UserInfoBase(BaseModel):
    user_id: str
    name: str
    email: EmailStr
    phone: Optional[str] = None
    corporation: Optional[str] = None
    business_number: Optional[int] = None


class UserInfoCreate(UserInfoBase):
    pass


class UserInfo(UserInfoBase):
    class Config:
        orm_mode = True
