from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from models import Base, User as UserModel, UserInfo as UserInfoModel
from core.database import engine, get_db
from crud import create_user_db, create_user_info_db, get_user, get_users
from schemas import User, UserCreate, UserInfo, UserInfoCreate

app = FastAPI()

# 데이터베이스 테이블 생성
Base.metadata.create_all(bind=engine)


@app.post("/users/", response_model=User)
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    db_user = get_user(db, user.user_id)
    if db_user:
        raise HTTPException(
            status_code=400, detail="User ID already registered")
    return create_user_db(db=db, user=user)


@app.get("/users/", response_model=List[User])  # 여기에서 List를 사용
def read_users(skip: int = 0, limit: int = 10, db: Session = Depends(get_db)):
    users = get_users(db, skip=skip, limit=limit)
    return users


@app.get("/users/{user_id}", response_model=User)
def read_user(user_id: str, db: Session = Depends(get_db)):
    db_user = get_user(db, user_id=user_id)
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user


@app.post("/user_info/", response_model=UserInfo)
def create_user_info(user_info: UserInfoCreate, db: Session = Depends(get_db)):
    db_user = get_user(db, user_info.user_id)
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return create_user_info_db(db=db, user_info=user_info)


@app.get("/user_info/{user_id}", response_model=UserInfo)
def read_user_info(user_id: str, db: Session = Depends(get_db)):
    db_user_info = db.query(UserInfoModel).filter(
        UserInfoModel.user_id == user_id).first()
    if db_user_info is None:
        raise HTTPException(status_code=404, detail="User Info not found")
    return db_user_info
