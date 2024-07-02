from sqlalchemy.orm import Session
from models import User as UserModel, UserInfo as UserInfoModel , emailAuth
from schemas import UserCreate , UserInfoCreate, User, UserBase, SendEmail, CheckEmail, CheckCode
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
        raise HTTPException(
            status_code=404, detail="해당 아이디의 유저가 없습니다.")  # 사용자가 존재하지 않음
    
    if not bcrypt_context.verify(user.password, find_user.password):
        raise HTTPException(
            status_code=401, detail="비밀번호가 일치하지 않습니다.")  # 비밀번호가 일치하지 않음
    # basemodel이 있는 경우 아래와 같이 return schema를 맞춰주는게 가독성이 더 좋은 것 같다.
    # return UserBase(email=find_user.email) 
    # login.py에 basemodel 이 없기 때문에 아래와 같은 형식으로 return
    # find_user
    return UserBase(email=find_user.email)  # 인증된 사용자 객체 반환

def email_auth(db: Session, user: CheckEmail):
    find_user = db.query(emailAuth).filter(emailAuth.email == user.email).first()
    return find_user

def update_email_auth(db: Session, user: CheckEmail, verify_code : str):
    email_auth_db = db.query(emailAuth).filter(emailAuth.email == user.email).first()
    if email_auth_db is None:
        return None
    email_auth_db.verify_number = verify_code
    db.commit()
    db.refresh(email_auth_db)
    return True

def create_email_auth(db: Session, user: CheckEmail, verify_code : str):
    email_auth_db = emailAuth(email=user.email, verify_number=verify_code,name = user.name)
    db.add(email_auth_db)
    db.commit()
    db.refresh(email_auth_db)
    return True

def update_is_active(db: Session, user: UserCreate):
    email_auth_db = db.query(emailAuth).filter(emailAuth.email == user.email).first()
    if email_auth_db is None:
        return None
    email_auth_db.is_active = True
    db.commit()
    db.refresh(email_auth_db)
    
    