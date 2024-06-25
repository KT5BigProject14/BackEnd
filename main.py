from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from models import Base
from core.database import engine, get_db
from crud import create_user_db
from schemas import User
app = FastAPI()

# 데이터베이스 테이블 생성
Base.metadata.create_all(bind=engine)

@app.post("/users/", response_model=User)
def create_user(user: User, db: Session = Depends(get_db)):
    print(user)
    # 조회를 해서 있는지 확인하고
    # 있다면 중복된 사용자라고 프론트에 전달
    # 없다면 create
    return create_user_db(db=db, user=user)

