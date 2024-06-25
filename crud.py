from sqlalchemy.orm import Session
from models import UserModel
from schemas import User
def get_user(db: Session, user_id: int):
    return db.query(User).filter(User.id == user_id).first()

def get_user_by_email(db: Session, email: str):
    return db.query(User).filter(User.email == email).first()

def create_user_db(db: Session, user: User):
    db_user = UserModel(
        name=user.name,
        email=user.email,
        hashed_password=user.hashed_password,
        phone=user.phone
    )
    db.add(db_user)
    db.commit()
    db.refresh(user)
    return user
