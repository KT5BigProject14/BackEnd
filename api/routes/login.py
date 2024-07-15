from fastapi import FastAPI, Depends, HTTPException, Response ,Request, Form
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from typing import List
from models import Base, User as UserModel, UserInfo as UserInfoModel
from core.database import engine, get_db
from crud.login_crud import create_user_db, create_user_info_db, get_user, get_users, authenticate_user, email_auth, update_email_auth, create_email_auth\
    ,update_is_active,create_google_user,update_new_random_password
from crud.info_crud import get_user_info_db
from schemas import User, UserCreate, UserInfo, UserInfoCreate, UserBase, JWTEncoder, JWTDecoder, SendEmail, MessageOk, CheckEmail, CheckCode
from typing import Annotated, Any
from fastapi import status
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from api.deps import JWTService
from core.config import settings
from fastapi.logger import logger
from starlette.background import BackgroundTasks
from starlette.requests import Request
from time import time, sleep
import yagmail
import secrets
import asyncio
import aiosmtplib
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from api.deps import JWTAuthentication
import requests
import jwt
import urllib.parse
from jwt import PyJWKClient
from fastapi.responses import RedirectResponse
from pydantic import EmailStr
import random
# from models import MessageOk, SendEmail
# import boto3
# from botocore.exceptions import ClientError


router = APIRouter()
jwt_service = JWTService(JWTEncoder(),JWTDecoder(),settings.ALGORITHM,settings.SECRET_KEY,settings.ACCESS_TOKEN_EXPIRE_TIME,settings.REFRESH_TOKEN_EXPIRE_TIME)
get_current_user = JWTAuthentication(jwt_service)
GetCurrentUser = Annotated[User, Depends(get_current_user)]
# 함수 예시 
# @router.get,post중 선택("들어오는 url", response_model="schemas에 정의 된 json데이터의 구조 프론트로 return할 때 사용")
# def 기능에_맞는_함수_이름(변수: schema에_정의된_프론트에서_인풋으로_받은_json_구조, db: Session = Depends(get_db)):
#     # db 작업 부분으로 보내는 코드
#     return crud에서_선언한_함수이름(db=db, crud에_선언한_인자_이름=crud로_보낼_데이터(프론트에서 가져온 데이터))

# oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

@router.post("/users/signup")
def create_user(user: UserBase, db: Session = Depends(get_db)):
    db_user = get_user(db, user.email)
    if db_user:
        raise HTTPException(
            status_code=400, detail="User ID already registered")
    update_is_active(db,user)
    create_user_db(db=db, user=user)
    return HTTPException(status_code=200,detail="signup success")

@router.post("/users/login")
async def login_user(
    user : User,
    db: Session = Depends(get_db)):
    user_id  = authenticate_user(db=db, user=user)
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    db_user_info = get_user_info_db(db= db, user=user_id.email)
    if db_user_info:
        data = {"email": str(user_id.email), "name": db_user_info.user_name, "role": user_id.role}
    else:
        data = {"email": str(user_id.email), "role":user_id.role}
        
    access_token = jwt_service.create_access_token(data)
    refresh_token = jwt_service.create_refresh_token(data)
    response = JSONResponse(content={"access_token":access_token,"email":user_id.email, "role": user_id.role}, status_code=status.HTTP_200_OK)
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        # secure=True,
        samesite='none',
    )
    return response

@router.get("/login/google")
async def auth_login():
    return {
            "url": f"https://accounts.google.com/o/oauth2/auth?response_type=code&client_id={settings.GOOGLE_CLIENT_ID}&redirect_uri={settings.GOOGLE_REDIRECT_URI}&scope=openid%20profile%20email&access_type=offline"
    }

@router.get("/login/oauth2/code/google")
async def auth_google(request: Request, response: Response, db: Session = Depends(get_db)):
    code = request.query_params.get('code')
    if not code:
        return RedirectResponse(url="http://localhost:3000/google/error")
    
    token_url = "https://oauth2.googleapis.com/token"
    data = {
        "code": code,
        "client_id": settings.GOOGLE_CLIENT_ID,
        "client_secret": settings.GOOGLE_CLIENT_SECRET,
        "redirect_uri": settings.GOOGLE_REDIRECT_URI,
        "grant_type": "authorization_code"
    }
    token_response = requests.post(token_url, data=data)
    
    if token_response.status_code != 200:
        return {"error": "Failed to get access token", "details": token_response.text}
    
    token_json = token_response.json()
    access_token = token_json.get("access_token")
    refresh_token = token_json.get("refresh_token")
    
    if not access_token:
        return {"error": "No access token received", "details": token_json}
    
    user_info_response = requests.get(
        "https://www.googleapis.com/oauth2/v1/userinfo",
        headers={"Authorization": f"Bearer {access_token}"}
    )

    if user_info_response.status_code != 200:
        return {"error": "Failed to fetch user info", "details": user_info_response.text}
    
    user_info = user_info_response.json()
    
    db_user = get_user(db, user_info['email'])
    if not db_user:
        create_google_user(db=db, user=user_info['email'])
    db_user_info = get_user_info_db(db= db, user=user_info['email'] )
    if db_user_info:
        role = None
        data = {"email": str(user_info['email']), "name": db_user_info.user_name, "role": "user"}
    else:
        role = "guest"
        data = {"email": str(user_info['email']), "role": "guest"}
    
    access_token = jwt_service.create_access_token(data)
    refresh_token = jwt_service.create_refresh_token(data)
    
    # 쿠키 설정

    
    # 리디렉션 응답
    # 이렇게 하면 query에 토큰값이랑 이메일 정보가 노출되어 보안적으로는 redis에 이 값들을 저장하고
    # 프론트에서 redirect 될면서 바로 redis값을 찾는 요청을 보내 return 해주는게 더 안전한 방법이긴 함
    # 아래와 같이 보내는 경우에는 query 값으로 sessionStorage에 저장한 후 바로 메인페이지로 redirect 해야함
    redirect_url = f"http://localhost:3000/google/login?token={access_token}&user={user_info['email']}&role={role}"
    response = RedirectResponse(url=redirect_url)
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=False,  # HTTPS 사용 시에만 True로 설정, 로컬 테스트라 False로 설정
        samesite='Lax',  # samesite는 'None', 'Lax', 'Strict' 중 하나여야 합니다. , 'Strict', 'None'은 HTTPS에서만 작동
    )
    return response

# 이메일 인증 보내는 로직(background로 멀티 스레드 작업을 통해 보내는 시간 단축)
@router.post("/email/send_by_gmail")
async def email_by_gmail(request: Request, mail: SendEmail, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    # email_auth DB조회
    selected_email = email_auth(db,mail)
    # 이미 있는 사용자이고, is_active True인 경우는 이미 등록된 사용자라고 에러 리턴
    if selected_email and selected_email.is_active == True:
        raise HTTPException(
            status_code=400, detail="This email already active")
    # 이미 있는 사용자이지만, is_active가 False인 경우 아래 task 실행하고 verify_number를 업데이트
    elif selected_email and selected_email.is_active == False :
        verification_code = ''.join(secrets.choice("0123456789") for _ in range(6))
        background_tasks.add_task(send_email, mail = mail.email,verification_code=verification_code)
        update_email_auth(db,mail,verification_code)
    # 없는 사용자인 경우 새로 db에 create
    else:
        t = time()
        verification_code = ''.join(secrets.choice("0123456789") for _ in range(6))
        background_tasks.add_task(send_email, mail = mail.email,verification_code=verification_code)
        print(str(round((time()-t)*1000,5))+"ms")
        create_email_auth(db,mail,verify_code = verification_code)
    return MessageOk()

@router.post("/find/password/send_by_gmail")
async def find_password_by_email(request: Request, mail: SendEmail, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    # email_auth DB조회
    selected_email = email_auth(db,mail)
    # 이미 회원가입을 끝낸유저만 찾기가 가능
    if selected_email and selected_email.is_active == True:
        verification_code = ''.join(secrets.choice("0123456789") for _ in range(6))
        background_tasks.add_task(send_email, mail = mail.email,verification_code=verification_code)
        update_email_auth(db,mail,verification_code)
    else:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="user not found")


#회원가입 이메일 검증
#비밀번호 찾기 이메일 검증
@router.put("/email/check_code")
async def check_code(user_code: CheckCode, db: Session = Depends(get_db)):
    selected_email = email_auth(db,user_code)
    twenty_four_hours_ago = datetime.utcnow() - timedelta(hours=24)
    if selected_email.updated_at < twenty_four_hours_ago:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Verification code expired")
    elif selected_email.verify_number == user_code.verify_code:
        raise  HTTPException(status_code=status.HTTP_200_OK, detail="verify_code is same")
    else:
        raise  HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="verify_code is different")

# 새로운 이메일 전송하는 코드        
@router.post("/send/new/password")
async def send_new_password(request: Request, mail: SendEmail, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    characters = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$%^&*"
    new_password = ''.join(random.choice(characters) for _ in range(10))
    update_new_random_password(mail,new_password,db)
    background_tasks.add_task(send_new_password, mail = mail.email,new_password=new_password)
    return HTTPException(status_code=status.HTTP_200_OK, detail="password change")


async def send_email(**kwargs):
    mail = kwargs.get("mail", None)
    verification_code = kwargs.get("verification_code", None)
    email_pw = settings.EMAIL_PW
    email_addr = settings.EMAIL_ADDR
    try:
        yag = yagmail.SMTP({email_addr: "Retriever"}, email_pw)
        # https://myaccount.google.com/u/1/lesssecureapps
        # 추후에 html 파일로 바꿈
        with open('templates/smtp_template.html', 'r', encoding='utf-8') as file:
            html_template = file.read()
        html_content = html_template.format(verification_code=verification_code)
        contents = [html_content]
        yag.send(mail, '[Retriever]이메일 인증을 위한 인증번호를 안내 드립니다.', contents)
    except Exception as e:
        print(e)
        
async def send_new_password(**kwargs):
    mail = kwargs.get("mail", None)
    new_password = kwargs.get("new_password", None)
    email_pw = settings.EMAIL_PW
    email_addr = settings.EMAIL_ADDR
    try:
        yag = yagmail.SMTP({email_addr: "Retriever"}, email_pw)
        with open('templates/smtp_password_template.html', 'r', encoding='utf-8') as file:
            html_template = file.read()
        html_content = html_template.format(new_password=new_password)
        contents = [html_content]
        yag.send(mail, '[Retriever]새로운 비밀번호를 알려드립니다.', contents)
    except Exception as e:
        print(e)
        
@router.post("/users/logout")
async def logout_user(response: Response, request: Request):
    refresh_token = request.cookies.get("refresh_token")
    response.delete_cookie(key="refresh_token")
    return HTTPException(status_code=status.HTTP_200_OK, detail="Logout successful")

@router.get("/users/", response_model=List[User])  # 여기에서 List를 사용
def read_users(skip: int = 0, limit: int = 10, db: Session = Depends(get_db)):
    users = get_users(db, skip=skip, limit=limit)
    return users


@router.get("/users/{email}", response_model=User)
def read_user(email: str, db: Session = Depends(get_db)):
    db_user = get_user(db, email=email)
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user


