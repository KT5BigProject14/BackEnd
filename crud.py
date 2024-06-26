from sqlalchemy.orm import Session
from models import User as UserModel, UserInfo as UserInfoModel
from schemas import UserCreate, UserInfoCreate, User as UserSchema


def create_user_db(db: Session, user: UserCreate):
    db_user = UserModel(user_id=user.user_id, password=user.password)
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


def get_user(db: Session, user_id: str):
    return db.query(UserModel).filter(UserModel.user_id == user_id).first()


def get_users(db: Session, skip: int = 0, limit: int = 10):
    return db.query(UserModel).offset(skip).limit(limit).all()
