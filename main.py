from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from models import Base, User
from core.database import engine, get_db
from crud import create_user

app = FastAPI()

# 데이터베이스 테이블 생성
Base.metadata.create_all(bind=engine)

@app.post("/users/", response_model=User)
def create_user(user: User, db: Session = Depends(get_db)):
    return create_user(db=db, user=user)

