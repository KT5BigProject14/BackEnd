from sqlalchemy.orm import Session
from models import QnA, Image
from schemas import Qna
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