from sqlalchemy.orm import Session
from models import User as UserModel, UserInfo as UserInfoModel
from schemas import UserCreate , UserInfoCreate, User
from passlib.context import CryptContext
from fastapi import FastAPI, Depends, HTTPException

bcrypt_context = CryptContext(schemes=['bcrypt'], deprecated = 'auto')

def create_user_db(db: Session, user: UserCreate):
    hashed_password = bcrypt_context.hash(user.password)
    
    db_user = UserModel(email=user.email, password=hashed_password)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


def create_user_info_db(db: Session, user_info: UserInfoCreate):
    db_user_info = UserInfoModel(**user_info.dict())
    db.add(db_user_info)
    db.commit()
    db.refresh(db_user_info)
    return db_user_info


def get_user(db: Session, email: str):
    return db.query(UserModel).filter(UserModel.email == email).first()


def get_users(db: Session, skip: int = 0, limit: int = 10):
    return db.query(UserModel).offset(skip).limit(limit).all()

def authenticate_user(db: Session, user:User ):
    find_user = db.query(UserModel).filter(UserModel.email == user.email).first()
    if not find_user:
        return None  # 사용자가 존재하지 않음
    
    if not bcrypt_context.verify(user.password, find_user.password):
        raise HTTPException(
            status_code=401, detail="비밀번호가 일치하지 않습니다.")  # 비밀번호가 일치하지 않음
    
    return user  # 인증된 사용자 객체 반환
