from sqlalchemy.orm import Session
from models import QnA, Image
from schemas import Qna, CheckQna
from passlib.context import CryptContext
from fastapi import FastAPI, Depends, HTTPException
from typing import Annotated
def create_qna(db: Session, qna: Qna):
    qna = QnA(email=qna.email, title=qna.title, content = qna.content)
    db.add(qna)
    db.commit()
    db.refresh(qna)
    return qna

def create_qna_image(db: Session, image:str, qna: Qna):
    qna_image = Image(image_name = image, qna_id = qna.qna_id)
    db.add(qna_image)
    db.commit()
    db.refresh(qna_image)
    return qna_image

def get_all_qna(db: Session):
    return db.query(QnA).all()
    
def get_qna(db:Session, qna_id : int):
    qna = db.query(QnA).filter(QnA.qna_id == qna_id).first()
    # qna_image = db.query(Image.image_name).filter(Image.qna_id == qna_id).all()
    # qna_image = [name[0] for name in qna_image]
    return qna

def update_qna(qna: CheckQna, db: Session):
    db_qna = db.query(QnA).filter(QnA.qna_id == qna.qna_id).first()
    db_qna.content = qna.content
    db_qna.title = qna.title
    db.commit()
    db.refresh(db_qna)
    return db_qna
    
def delete_qna(qna: CheckQna, db:Session):
    qna_to_delete = db.query(QnA).filter(QnA.qna_id == qna.qna_id).first()
    db.delete(qna_to_delete)
    db.commit()