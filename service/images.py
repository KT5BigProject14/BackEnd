from fastapi import APIRouter, UploadFile, HTTPException, status, Depends



from typing import Annotated
from fastapi import UploadFile, File
import secrets
import io
from PIL import Image, ImageOps
from boto3 import client
from core.config import settings



# 이미지 확장자 명 확인
async def validate_image_type(file: UploadFile) -> UploadFile:
    if file.filename.split(".")[-1].lower() not in ["jpg", "jpeg", "png"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="업로드 불가능한 이미지 확장자입니다.",
        )
 
    if not file.content_type.startswith("image"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="이미지 파일만 업로드 가능합니다.",
        )
    return file

# 이미지 사이즈 크기 체크
async def validate_image_size(file: UploadFile) -> UploadFile:
    if len(await file.read()) > 10 * 1024 * 1024:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="이미지 파일은 10MB 이하만 업로드 가능합니다.",
        )
    return file

# 파일 이름 변경
def change_filename(file: UploadFile) -> UploadFile:
    """
    이미지 이름 변경
    """
    random_name = secrets.token_urlsafe(16)
    file.filename = f"{random_name}.jpeg"
    return file

# 이미지 최적 사이즈로 resize
def resize_image(file: UploadFile, max_size: int = 1024):
    read_image = Image.open(file.file)
    original_width, original_height = read_image.size
 
    if original_width > max_size or original_height > max_size:
        if original_width > original_height:
            new_width = max_size
            new_height = int((new_width / original_width) * original_height)
        else:
            new_height = max_size
            new_width = int((new_height / original_height) * original_width)
        read_image = read_image.resize((new_width, new_height))
 
    read_image = read_image.convert("RGB")
    read_image = ImageOps.exif_transpose(read_image)
    return read_image

# 테스트용 로컬 저장
def save_image_to_filesystem(image: Image, file_path: str):
    image.save(file_path, "jpeg", quality=70)
    return file_path

# AWS S3 저장하기위해 바이트 코드로 변환
def convert_image_to_bytes(image: Image) -> io.BytesIO:
    img_byte = io.BytesIO()
    image.save(img_byte, "jpeg", quality=70)
    img_byte.seek(0)
    return img_byte

# AWS SDK boto3의 client
s3_client = client(
    "s3",
    aws_access_key_id=settings.AWS_ACCESS_KEY, # 본인 소유의 키를 입력
    aws_secret_access_key=settings.AWS_SECRET_KEY, # 본인 소유의 키를 입력
    region_name=settings.REGIONE_NAME,
)
# S3에 업로드
def upload_to_s3(file: io.BytesIO, bucket_name: str, file_name: str) -> None:
    s3_client.upload_fileobj(
        file,
        bucket_name,
        file_name,
        ExtraArgs={"ContentType": "image/jpeg"},
    )