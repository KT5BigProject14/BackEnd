from sqlalchemy.orm import Session
from models import User as UserModel, UserInfo as UserInfoModel , emailAuth 
from schemas import UserCreate , UserInfoCreate, User, UserBase, SendEmail, CheckEmail, CheckCode , UserInfoBase
from passlib.context import CryptContext
from fastapi import FastAPI, Depends, HTTPException
from typing import Annotated
def create_user_info_db(db: Session, user_info: UserInfoBase):
    db_user_info = UserInfoModel(email = user_info.email, corporation = user_info.corporation, business_number = user_info.business_number, 
                                 position =user_info.position, phone = user_info.phone)
    db.add(db_user_info)
    db.commit()
    db.refresh(db_user_info)
    return db_user_info

def update_user_info_db(db: Session, user_info: UserInfoBase):
    db_user_info = db.query(UserInfoModel).filter(UserInfoModel.email == user_info.email).first()
    if db_user_info is None:
        return None
    db_user_info.corporation = user_info.corporation, 
    db_user_info.business_number = user_info.business_number, 
    db_user_info.position =user_info.position, 
    db_user_info.phone = user_info.phone
    db.commit()
    db.refresh(db_user_info)

