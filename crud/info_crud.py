from sqlalchemy.orm import Session
from models import User as UserModel, UserInfo as UserInfoModel , EmailAuth, Keyword
from schemas import UserCreate , UserInfoCreate, User, UserBase, SendEmail, CheckEmail, CheckCode , UserInfoBase, ChangePassword, Keywords
from passlib.context import CryptContext
from fastapi import FastAPI, Depends, HTTPException
from typing import Annotated
from pydantic import EmailStr

def create_user_info_db(db: Session, user_info: UserInfoBase, email: EmailStr):
    db_user_info = UserInfoModel(email = email, corporation = user_info.corporation, business_number = user_info.business_number, 
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

def update_user_info_db(db: Session, user_info: UserInfoBase, user_email: EmailStr):
    db_user_info = db.query(UserInfoModel).filter(UserInfoModel.email == user_email).first()
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

def create_keyword_db(keyword: Keywords, email: EmailStr, db :Session):
    db_keyword = Keyword(email = email, likeyear = keyword.likeyear, likecountry = keyword.likecountry, likebusiness =keyword.likebusiness)
    db.add(db_keyword)
    db.commit()
    db.refresh(db_keyword)
    return db_keyword
def get_user_keyword(email: EmailStr, db :Session):
    db_keyword = db.query(Keyword).filter(Keyword.email == email).first()
    if db_keyword is None:
        return None
    else:
        return db_keyword
def update_keyword_db(keyword: Keywords, email: EmailStr, db :Session):
    db_keyword = db.query(Keyword).filter(Keyword.email == email).first()
    db_keyword.likebusiness = keyword.likebusiness
    db_keyword.likecountry = keyword.likecountry
    db_keyword.likeyear = keyword.likeyear
    db.commit()
    db.refresh(db_keyword)