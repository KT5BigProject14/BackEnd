from sqlalchemy.orm import Session
from models import User as UserModel, UserInfo as UserInfoModel , emailAuth 
from schemas import UserCreate , UserInfoCreate, User, UserBase, SendEmail, CheckEmail, CheckCode , UserInfoBase, ChangePassword
from passlib.context import CryptContext
from fastapi import FastAPI, Depends, HTTPException
from typing import Annotated
from pydantic import EmailStr

def create_user_info_db(db: Session, user_info: UserInfoBase):
    db_user_info = UserInfoModel(email = user_info.email, corporation = user_info.corporation, business_number = user_info.business_number, 
                                 position =user_info.position, phone = user_info.phone, user_name = user_info.user_name)
    db.add(db_user_info)
    db.commit()
    db.refresh(db_user_info)
    return db_user_info

def get_user_info_db(db: Session, user: EmailStr):
    db_user_info = db.query(UserInfoModel).filter(UserInfoModel.email == user).first()
    if db_user_info is None:
        return None
    else:
        return db_user_info

def update_user_info_db(db: Session, user_info: UserInfoBase):
    db_user_info = db.query(UserInfoModel).filter(UserInfoModel.email == user_info.email).first()
    if db_user_info is None:
        return None
    db_user_info.corporation = user_info.corporation, 
    db_user_info.business_number = user_info.business_number, 
    db_user_info.position =user_info.position, 
    db_user_info.phone = user_info.phone
    db_user_info.user_name = user_info.user_name
    db.commit()
    db.refresh(db_user_info)

def change_user_role(db:Session, user: str):
    db_user = db.query(UserModel).filter(UserModel.email == user).first()
    db_user.role = "user"
    db.commit()
    db.refresh(db_user)
    return db_user