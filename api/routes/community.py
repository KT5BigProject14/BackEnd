import service.images as images
from crud.community_crud import create_community, create_community_image, read_all_community, get_community, db_update_community, db_delete_community, delete_community_img, create_community_comment, get_community_comment, update_community_comment, delete_community_comment
from schemas import Community, CheckCommunity, CommunityComment, CheckCommunityComment
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
async def upload_qna(request: Request, title: Annotated[str, Form()], content: Annotated[str, Form()], images: List[UploadFile] = File([]), db: Session = Depends(get_db)):

    community_data = {"email": request.state.user.email,
                      "title": title, "content": content}
    community = Community(**community_data)  # Qna 모델 인스턴스 생성
    # qna 글 저장 return 값은 해당글 정보
    created_community = create_community(db=db, community=community)
    image_filenames = []
    # 여러 파일이 왔을 때 for문으로 이미지 저장
    # created_qna에서 qna_id를 넣어 나중에 조회할때 선택한 qna 글에 대한 모든 이미지를 조회하기 위해 사용
    for image in images:
        filename = await upload_image(image)
        create_community_image(db=db, image=filename,
                               community=created_community)
        image_filenames.append(filename)
    return HTTPException(status_code=status.HTTP_200_OK, detail="upload successful")


@router.get("/load/all")
async def load_all_community(request: Request, db: Session = Depends(get_db)):
    all_community = read_all_community(db=db)
    return all_community

@router.get("/load/{community_id}")
async def load_community(request: Request, community_id: int, db: Session = Depends(get_db)):
    result = get_community(db, community_id, email = request.state.user.email)
    community_comments = get_community_comment(db=db, community_id=community_id,email = request.state.user.email)
    qna_images = []

    if result['community_images']:
        for image_name in result['community_images']:
            image_path = os.path.join("./img", image_name)
            if os.path.exists(image_path):
                encoded_image = images.encode_image_to_base64(image_path)
                qna_images.append({
                    image_name: encoded_image,
                })

    community_dict = {
        "title": result['community'].title,
        "content": result['community'].content,
        "email": result['community'].email,
        "community_id": result['community'].community_id,
        "created_at": result['community'].created_at.isoformat(),
        "corporation": result['community'].corporation,
        "is_my_post" : result['community'].is_my_post
    }

    community_comment_response = [
        {
            "community_comment_id": community_comment.community_comment_id,
            "content": community_comment.content,
            "created_at": community_comment.created_at.isoformat(),
            "qna_id": community_comment.community_id,
            "email": community_comment.email,
            "corporation": community_comment.corporation,
            "is_my_post": community_comment.is_my_post
            
        }
        for community_comment in community_comments
    ]

    response_content = {
        "result": {
            "community": community_dict,
            "community_images": qna_images
        },
        "comment": community_comment_response
    }
    return JSONResponse(content=response_content)


@router.put("/edit")
async def update_community(
    request: Request,
    community_id: Annotated[int, Form()],
    email: Annotated[str, Form()],
    title: Annotated[str, Form()],
    content: Annotated[str, Form()],
    image: List[UploadFile] = File([]),
    db: Session = Depends(get_db)
):
    user = request.state.user
    if user.email == email:
        # QnA 데이터 처리 로직
        community_comments_data = {
            "community_id": community_id, "email": email, "title": title, "content": content}
        community = CheckCommunity(**community_comments_data)
        result = db_update_community(community=community, db=db)

        # 이미지 처리 로직
        deleted_images = delete_community_img(community, db)
        if deleted_images:
            for deleted_imgs in deleted_images:
                filename = deleted_imgs.image_name
                images.delete_file_from_filesystem(f"./img/{filename}")

        image_filenames = []
        if image:
            for img in image:
                filename = await upload_image(img)
                create_community_image(db=db, image=filename, community=result)
                image_filenames.append(filename)

        return {"community": community, "img": image_filenames}
    else:
        raise HTTPException(status_code=400, detail="You are not the writer")


@router.delete("/delete")
async def delete_qna(community: CheckCommunity, request: Request, db: Session = Depends(get_db)):
    user = request.state.user
    if community.email == user.email or user.role == "admin":
        deleted_images = delete_community_img(community, db)
        db_delete_community(community, db)
        if deleted_images:
            for deleted_img in deleted_images:
                filename = deleted_img.image_name
                images.delete_file_from_filesystem(f"./img/{filename}")
        return HTTPException(status_code=200, detail="delete_sucess")
    else:
        raise HTTPException(status_code=400, detail="you are not writer")


@router.post("/upload/comment")
async def upload_qna(request: Request, community_comment: CommunityComment, db: Session = Depends(get_db)):
    user = request.state.user
    community_comment = create_community_comment(
        db=db, community_comment=community_comment, email=user.email)
    return community_comment


@router.put("/update/comment")
async def load_qna(request: Request, community_comment: CheckCommunityComment, db: Session = Depends(get_db)):
    user = request.state.user
    if community_comment.email == user.email:
        result = update_community_comment(community_comment, db)
        return result
    else:
        raise HTTPException(status_code=400, detail="you are not writer")


@router.delete("/delete/comment")
async def load_qna(community_comment: CheckCommunityComment, request: Request, db: Session = Depends(get_db)):
    user = request.state.user
    if community_comment.email == user.email:
        delete_community_comment(community_comment, db)
        return HTTPException(status_code=200, detail="delete_sucess")
    else:
        raise HTTPException(status_code=400, detail="you are not writer")
