from sqlalchemy.orm import Session
from models import QnA, Image, Comment
from schemas import Qna, CheckQna, CheckComment
from passlib.context import CryptContext
from fastapi import FastAPI, Depends, HTTPException
from typing import Annotated
from pydantic import EmailStr
def create_qna(db: Session, qna: Qna):
    qna = QnA(email=qna.email, title=qna.title, content = qna.content)
    db.add(qna)
    db.commit()
    db.refresh(qna)
    return qna

def create_qna_image(db: Session, image:str, qna: CheckQna):
    qna_image = Image(image_name = image, qna_id = qna.qna_id)
    db.add(qna_image)
    db.commit()
    db.refresh(qna_image)
    return qna_image

def user_all_qna(db: Session, email: EmailStr):
    user_qna = db.query(QnA).filter(QnA.email == email).all()
    admin_qna = db.query(QnA).filter(QnA.email == "admin@example.com").all()
    return {"user_qna": user_qna, "admin_qna": admin_qna}

def admin_all_qna(db:Session):
    return db.query(QnA).all()

def get_qna(db:Session, qna_id : int):
    qna = db.query(QnA).filter(QnA.qna_id == qna_id).first()
    qna_image = db.query(Image.image_name).filter(Image.qna_id == qna_id).all()
    qna_image = [name[0] for name in qna_image]
    return {"qna":qna, "qna_images":qna_image}

def db_update_qna(qna: CheckQna, db: Session):
    db_qna = db.query(QnA).filter(QnA.qna_id == qna.qna_id).first()
    if not db_qna:
        raise HTTPException(status_code=404, detail="QnA not found")
    db_qna.content = qna.content
    db_qna.title = qna.title
    db.commit()
    db.refresh(db_qna)
    return db_qna

def delete_img(qna: CheckQna, db: Session):
    images_to_delete = db.query(Image).filter(Image.qna_id == qna.qna_id).all()
    for db_img in images_to_delete:
        db.delete(db_img)
    db.commit()
    return images_to_delete

def delete_qna(qna: CheckQna, db:Session):
    qna_to_delete = db.query(QnA).filter(QnA.qna_id == qna.qna_id).first()
    db.delete(qna_to_delete)
    db.commit()
    
def create_comment(comment: Comment, db: Session):
    new_comment = Comment(qna_id = comment.qna_id, email = comment.email, content = comment.content)
    db.add(new_comment)
    db.commit()
    db.refresh(new_comment)
    return new_comment

def get_comment(qna_id: int , db: Session):
    return db.query(Comment).filter(Comment.qna_id == qna_id).all()

def update_comment(comment: CheckComment, db: Session):
    target_comment = db.query(Comment).filter(Comment.comment_id == comment.comment_id).first()
    target_comment.content = comment.content
    db.commit()
    db.refresh(target_comment)
    return target_comment

def delete_comment(comment : CheckComment, db: Session):
    comment_to_delete = db.query(Comment).filter(Comment.comment_id == comment.comment_id).first()
    db.delete(comment_to_delete)
    db.commit()