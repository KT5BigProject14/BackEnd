import service.images as images
from crud.qna_crud import create_qna, create_qna_image, get_all_qna,get_qna, db_update_qna, delete_qna, delete_img, create_comment, get_comment, update_comment, delete_comment
from schemas import Qna, CheckQna, Comment, CheckComment
from fastapi.security import OAuth2PasswordBearer
from fastapi import APIRouter, UploadFile, HTTPException, status, Depends, Form
from fastapi.responses import JSONResponse
from typing import List
import os
import base64
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
from pydantic import BaseModel, EmailStr
router = APIRouter()

# File을 그냥 Optional로 지정했음


async def upload_image(file: UploadFile | None):
    """
    이미지 업로드 테스트
    - 1. 클라이언트에서 서버로 이미지를 업로드한다.
    - 2. 이미지 확장자가 업로드 가능한지 확인한다.
    - 3. 이미지 사이즈가 업로드 가능한 크기인지 확인한다.
    - 4. 이미지 이름을 변경한다.
    - 5. 이미지를 최적화하여 저장한다.
    """
    if not file:
        return {"detail": "이미지 없음"}

    file = await images.validate_image_type(file)
    file = await images.validate_image_size(file)
    file = images.change_filename(file)
    filename = file.filename
    image = images.resize_image(file)
    # image = images.convert_image_to_bytes(image)
    # upload_to_s3(image,"bucket_name", filename)
    image = images.save_image_to_filesystem(image, f"./img/{filename}")

    return filename
ImageUploader = Annotated[dict, Depends(upload_image)]

jwt_service = JWTService(JWTEncoder(), JWTDecoder(), settings.ALGORITHM, settings.SECRET_KEY,
                         settings.ACCESS_TOKEN_EXPIRE_TIME, settings.REFRESH_TOKEN_EXPIRE_TIME)

get_current_user = JWTAuthentication(jwt_service)
GetCurrentUser = Annotated[User, Depends(get_current_user)]

# file 데이터는 form전송으로 진행되기 때문에 다 form형식으로 받아와야해서 아래와 같이 pydentic으로 한 번에 받지 못함


@router.post("/upload")
async def upload_qna(email: Annotated[str, Form()], title: Annotated[str, Form()], content: Annotated[str, Form()], images: List[UploadFile] = File([]), db: Session = Depends(get_db)):
    qna_data = {"qna_email": email, "title": title, "content": content}
    qna = Qna(**qna_data)  # Qna 모델 인스턴스 생성
    # qna 글 저장 return 값은 해당글 정보
    created_qna = create_qna(db=db, qna=qna)
    image_filenames = []
    # 여러 파일이 왔을 때 for문으로 이미지 저장
    # created_qna에서 qna_id를 넣어 나중에 조회할때 선택한 qna 글에 대한 모든 이미지를 조회하기 위해 사용
    for image in images:
        filename = await upload_image(image)
        create_qna_image(db=db, image=filename, qna=created_qna)
        image_filenames.append(filename)
    return HTTPException(status_code=status.HTTP_200_OK, detail="upload successful" )

@router.get("/load_all_qna")
async def load_all_qna(db: Session = Depends(get_db)):
    return get_all_qna(db)

@router.get("/load_qna/{qna_id}")
async def load_qna(qna_id: int ,db: Session = Depends(get_db)):
    result = get_qna(db, qna_id)
    comments = get_comment(db = db, qna_id = qna_id)
    if result['qna_image']:
        qna_images = []
        for image_name in result['qna_image']:
            image_path = os.path.join("./img", image_name)
            if os.path.exists(image_path):
                encoded_image = images.encode_image_to_base64(image_path)
                qna_images.append({
                    image_name: encoded_image,
                })
        qna_dict = {
            "title": result['qna'].title,
            "content": result['qna'].content,
            "qna_email": result['qna'].email,
            "qna_id": result['qna'].qna_id,
            "created_at": result['qna'].created_at.isoformat()
        }
        comment_response = [
            {
                "comment_id": comment.comment_id,
                "content": comment.content,
                "created_at": comment.created_at.isoformat() ,
                "qna_id": comment.qna_id,
                "email": comment.email
            } 
            for comment in comments
            ]

        response_content = {
            "result":{
                "qna": qna_dict,
                "qna_images": qna_images
            },
            "comment":comment_response
        }
        return JSONResponse(content=response_content)
    else:
        return {"result": result, "comment": comments}
    
@router.put("/update_qna")
async def update_qna(
    email: EmailStr,
    qna_id: Annotated[int, Form()],
    qna_email: Annotated[str, Form()],
    title: Annotated[str, Form()],
    content: Annotated[str, Form()],
    image: Optional[List[UploadFile]] = File([]),
    db: Session = Depends(get_db)
):
    if qna_email == email:
        # QnA 데이터 처리 로직
        qna_data = {"qna_id": qna_id, "qna_email": qna_email, "title": title, "content": content}
        qna = CheckQna(**qna_data)
        result = db_update_qna(qna=qna, db=db)
        
        # 이미지 처리 로직
        deleted_images = delete_img(qna, db)
        for deleted_imgs in deleted_images:
            filename = deleted_imgs.image_name
            images.delete_file_from_filesystem(f"./img/{filename}")

        image_filenames = []
        if image:
            for img in image:
                filename = await upload_image(img)
                create_qna_image(db=db, image=filename, qna_id=qna_id)
                image_filenames.append(filename)

        return {"qna": qna, "img": image_filenames}
    else:
        raise HTTPException(status_code=400, detail="You are not the writer")
    
@router.delete("/delete_qna")
async def load_qna(qna: CheckQna ,email: EmailStr ,db: Session = Depends(get_db)):
    if qna.qna_email == email:
        deleted_images = delete_img(qna, db)
        delete_qna(qna,db)
        for deleted_img in deleted_images:
            filename = deleted_img.image_name
            images.delete_file_from_filesystem(f"./img/{filename}")
        return HTTPException(status_code=200, detail="delete_sucess")   
    else:
        raise HTTPException(status_code=400, detail="you are not writer")  

@router.post("/upload/comment")
async def upload_qna(comment: Comment,db: Session = Depends(get_db)):
    comment = create_comment(db=db, comment = comment)
    return comment

@router.put("/update/comment")
async def load_qna(comment: CheckComment ,email: EmailStr ,db: Session = Depends(get_db)):
    if comment.email == email:
        result = update_comment(comment,db)
        return result   
    else:
        raise HTTPException(status_code=400, detail="you are not writer")
             
@router.delete("/delete/comment")
async def load_qna(qna: CheckComment ,email: EmailStr ,db: Session = Depends(get_db)):
    if qna.email == email:
        delete_comment(qna,db)
        return HTTPException(status_code=200, detail="delete_sucess")   
    else:
        raise HTTPException(status_code=400, detail="you are not writer")  
