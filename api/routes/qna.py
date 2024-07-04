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
router = APIRouter()
import service.images as images 
from fastapi.security import OAuth2PasswordBearer
from schemas import Qna
from crud.qna_crud import create_qna, create_qna_image
from core.database import engine, get_db
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJlbWFpbCI6InVzZXJAZXhhbXBsZS5jb20iLCJleHAiOjE3MjAwNzIzOTB9.5IK8VdbtZLD0qSzUCII8hlYETDVUDkwFbsmohrmPaI8")

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
jwt_service = JWTService(JWTEncoder(),JWTDecoder(),settings.ALGORITHM,settings.SECRET_KEY,settings.ACCESS_TOKEN_EXPIRE_TIME,settings.REFRESH_TOKEN_EXPIRE_TIME)

get_current_user = JWTAuthentication(jwt_service)
GetCurrentUser = Annotated[User, Depends(get_current_user)]

# file 데이터는 form전송으로 진행되기 때문에 다 form형식으로 받아와야해서 아래와 같이 pydentic으로 한 번에 받지 못함
@router.post("/upload")
async def upload_qna(email: Annotated[str, Form()],title: Annotated[str, Form()],content: Annotated[str, Form()],images: Optional[List[UploadFile]] = File([]) ,db: Session = Depends(get_db)):
    qna_data = {"email": email, "title": title, "content": content}
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
    return {"qna": created_qna, "images": image_filenames}

