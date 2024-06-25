from sqlalchemy import Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from pydantic import BaseModel, EmailStr


Base = declarative_base()

class UserModel(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), index=True) 
    email = Column(String(255), unique=True, index=True)  
    hashed_password = Column(String(255)) 
    phone = Column(String(20))
