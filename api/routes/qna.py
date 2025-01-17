import service.images as images
from crud.qna_crud import create_qna, create_qna_image,get_qna, db_update_qna, db_delete_qna, delete_img, create_comment, get_comment, update_comment, delete_comment, user_all_qna,admin_all_qna
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
from starlette.requests import Request

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
    # s3 사용시 필요
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
async def upload_qna(request: Request,title: Annotated[str, Form()], content: Annotated[str, Form()], images: List[UploadFile] = File([]), db: Session = Depends(get_db)):
    
    try:
        qna_data = {"email": request.state.user.email, "title": title, "content": content}
        qna = Qna(**qna_data)  # Qna 모델 인스턴스 생성

        # qna 글 저장 return 값은 해당글 정보
        created_qna = create_qna(db=db, qna=qna)
        image_filenames = []

        # 여러 파일이 왔을 때 for문으로 이미지 저장
        # created_qna에서 qna_id를 넣어 나중에 조회할때 선택한 qna 글에 대한 모든 이미지를 조회하기 위해 사용
        for image in images:
            # 로직상 글이 생성되어야 이미지 업로드 가능하기 때문에 프론트에서 업로드되는 파일 확장자가 한번 검증을 거친다는 가정하에 설계 
            # 이미지 업로드 중 허용되지 않는 파일 형식은 업로드 불가능
            filename = await upload_image(image)
            create_qna_image(db=db, image=filename, qna=created_qna)
            image_filenames.append(filename)

        return {"status_code": status.HTTP_200_OK, "detail": "Upload successful"}

    except Exception as e:
        db.rollback()  # db rollback
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    finally:
        db.close()  

# 모든 qna를 가져오는 api
@router.get("/load/all/qna")
async def load_user_all_qna(request: Request, db: Session = Depends(get_db)):
    user = request.state.user
    # user일땐 user의 qna와 admin의 qna만 가져옴
    if user.role == "user":
        return user_all_qna(db, user.email)
    # admin인 경우 모든 user의 qna를 가져옴
    elif user.role =="admin":
        return admin_all_qna(db)
    else:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="you are not authorized")
    
# user가 선택한 qna를 가져오는 api
@router.get("/load_qna/{qna_id}")
async def load_qna(qna_id: int, db: Session = Depends(get_db)):
    result = get_qna(db, qna_id)
    comments = get_comment(db=db, qna_id=qna_id)
    qna_images = []
    
    # 이미지를 base64인코딩 하여 json으로 전송
    if result['qna_images']:
        for image_name in result['qna_images']:
            image_path = os.path.join("./img", image_name)
            if os.path.exists(image_path):
                encoded_image = images.encode_image_to_base64(image_path)
                qna_images.append({
                    image_name: encoded_image,
                })
    # qna 관련 데이터
    qna_dict = {
        "title": result['qna'].title,
        "content": result['qna'].content,
        "email": result['qna'].email,
        "qna_id": result['qna'].qna_id,
        "created_at": result['qna'].created_at.isoformat()
    }
    # 댓글 관련 데이터
    comment_response = [
        {
            "comment_id": comment.comment_id,
            "content": comment.content,
            "created_at": comment.created_at.isoformat(),
            "qna_id": comment.qna_id,
            "email": comment.email
        }
        for comment in comments
    ]
    # 최종적으로 프론트로 보낼 딕셔너리
    response_content = {
        "result": {
            "qna": qna_dict,
            "qna_images": qna_images
        },
        "comment": comment_response
    }
    return JSONResponse(content=response_content)

# 글 수정
@router.put("/edit")
async def update_qna(
    request:Request,
    qna_id: Annotated[int, Form()],
    email: Annotated[str, Form()],
    title: Annotated[str, Form()],
    content: Annotated[str, Form()],
    image: List[UploadFile] = File([]),
    db: Session = Depends(get_db)
):
    user = request.state.user
    # 글을 쓴 유저와 현재 로그인 된 유저가 같아야 수정 가능
    if user.email == email:
        # QnA 데이터 처리 로직
        qna_data = {"qna_id": qna_id, "email": email, "title": title, "content": content}
        qna = CheckQna(**qna_data)
        result = db_update_qna(qna=qna, db=db)
        
        # 이미지 처리 로직
        # 모든 이미지를 삭제하고 다시 삽입
        deleted_images = delete_img(qna, db)
        if deleted_images:
            for deleted_imgs in deleted_images:
                filename = deleted_imgs.image_name
                images.delete_file_from_filesystem(f"./img/{filename}")

        image_filenames = []
        if image:
            for img in image:
                filename = await upload_image(img)
                create_qna_image(db=db, image=filename, qna=result)
                image_filenames.append(filename)

        return {"qna": qna, "img": image_filenames}
    else:
        raise HTTPException(status_code=400, detail="You are not the writer")

# 이미지 삭제 api    
@router.delete("/delete")
async def delete_qna(qna: CheckQna ,request:Request ,db: Session = Depends(get_db)):
    user = request.state.user
    if qna.email == user.email or user.role == "admin":
        deleted_images = delete_img(qna, db)
        db_delete_qna(qna,db)
        if deleted_images:
            for deleted_img in deleted_images:
                filename = deleted_img.image_name
                images.delete_file_from_filesystem(f"./img/{filename}")
        return HTTPException(status_code=200, detail="delete_sucess")   
    else:
        raise HTTPException(status_code=400, detail="you are not writer")  

# 댓글 업로드
@router.post("/upload/comment")
async def upload_qna(request: Request, comment: Comment,db: Session = Depends(get_db)):
    user = request.state.user
    comment = create_comment(db=db, comment = comment, email = user.email )
    return comment

# 댓글 수정 api
@router.put("/update/comment")
async def load_qna(request: Request, comment: CheckComment  ,db: Session = Depends(get_db)):
    user = request.state.user
    if comment.email == user.email:
        result = update_comment(comment,db)
        return result   
    else:
        raise HTTPException(status_code=400, detail="you are not writer")

#  글 삭제 api           
@router.delete("/delete/comment")
async def load_qna(comment: CheckComment ,request: Request ,db: Session = Depends(get_db)):
    user = request.state.user
    if comment.email == user.email:
        delete_comment(comment,db)
        return HTTPException(status_code=200, detail="delete_sucess")   
    else:
        raise HTTPException(status_code=400, detail="you are not writer")  
