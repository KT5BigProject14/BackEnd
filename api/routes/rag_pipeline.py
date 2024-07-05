import service.images as images
from crud.qna_crud import create_qna, create_qna_image
from schemas import Qna
from fastapi.security import OAuth2PasswordBearer
from fastapi import APIRouter, UploadFile, HTTPException, status, Depends, Form


from api.deps import JWTAuthentication
from typing import Annotated, Optional
from schemas import User, JwtUser
from sqlalchemy.orm import Session
from core.database import engine, get_db
from api.deps import JWTService
from schemas import JWTEncoder, JWTDecoder
from typing import Annotated, List
from fastapi import UploadFile, File
import secrets
import io
from PIL import Image, ImageOps
from boto3 import client
from core.config import settings
from RAGPipeLine import Ragpipeline

router = APIRouter()


def get_rag_pipeline():
    return Ragpipeline()


@router.post("/chat/")
async def chat(question: str, session_id: str, rag_pipeline: Ragpipeline = Depends(get_rag_pipeline)):
    response = rag_pipeline.chat_generation(question, session_id)
    return {"response": response}


@router.post("/update_vector_db/")
async def update_vector_db(file: UploadFile = File(...), rag_pipeline: Ragpipeline = Depends(get_rag_pipeline)):
    file_object = file.file
    filename = file.filename
    success = rag_pipeline.update_vector_db(file_object, filename)
    if success:
        return {"message": "Vector store updated successfully"}
    else:
        return {"message": "Document is too similar to existing documents"}
