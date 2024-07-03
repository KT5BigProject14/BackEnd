from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from models import UserInfo
from core.database import engine, get_db
from crud.info_crud import update_user_info_db
from schemas import UserInfoBase, User

router = APIRouter()

@router.get("/user_info/{email}")
def read_user_info(email: str, db: Session = Depends(get_db)):
    db_user_info = db.query(UserInfo).filter(UserInfo.email == email).first()
    if db_user_info is None:
        raise HTTPException(status_code=404, detail="User Info not found")
    return db_user_info

@router.put("/user_info/")
def update_user_info(user_info: UserInfoBase ,db: Session = Depends(get_db)):
    update_user_info_db(db, user_info)
    return HTTPException(status_code=200, detail="update_user_info")
    