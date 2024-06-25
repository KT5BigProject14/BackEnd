from sqlalchemy import Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from pydantic import BaseModel, EmailStr

Base = declarative_base()

class User(BaseModel):
    id: int
    name: str
    email: EmailStr
    hashed_password: str

    class Config:
        orm_mode = True
