from fastapi import FastAPI, Depends, HTTPException, Response ,Request, Form
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from typing import List
from models import Base, User as UserModel, UserInfo as UserInfoModel
from core.database import engine, get_db
from crud.login_crud import create_user_db, create_user_info_db, get_user, get_users, authenticate_user, email_auth, update_email_auth, create_email_auth\
    ,update_is_active,create_google_user,update_new_random_password,create_admin
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

#회원 가입
@router.post("/signup")
def create_user(user: UserBase, db: Session = Depends(get_db)):
    db_user = get_user(db, user.email)
    if db_user:
        raise HTTPException(
            status_code=400, detail="User ID already registered")
    update_is_active(db,user)
    create_user_db(db=db, user=user)
    return HTTPException(status_code=200,detail="signup success")

# 일반 로그인 
@router.post("/login")
async def login_user(
    user : User,
    db: Session = Depends(get_db)):
    user_id  = authenticate_user(db=db, user=user)
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    db_user_info = get_user_info_db(db= db, user=user_id.email)
    if db_user_info:
        data = {"email": str(user_id.email),"type":"normal", "name": db_user_info.user_name, "role": user_id.role}
    else:
        data = {"email": str(user_id.email),"type":"normal", "role":user_id.role}
        
    access_token = jwt_service.create_access_token(data)
    refresh_token = jwt_service.create_refresh_token(data)
    # access_token 프론트로 전달
    response = JSONResponse(content={"access_token":access_token, "type":"normal","role": user_id.role}, status_code=status.HTTP_200_OK)
    # refresh_token 쿠키에 set
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True, # 프론트엔드에서 쿠키를 조작할 수 없음
        secure=False,  # HTTPS 사용 시에만 True로 설정, 로컬 테스트라 False로 설정
        samesite='Lax',  # samesite는 'None', 'Lax', 'Strict' 중 하나여야 합니다. , 'Strict', 'None'은 HTTPS에서만 작동
    )
    return response

# 구글 로그인 uri 
# 구글 redirect uri는 localhost일때 제외하고 https여야 함
@router.get("/login/google")
async def auth_google_login():
    return {
            "url": f"https://accounts.google.com/o/oauth2/auth?response_type=code&client_id={settings.GOOGLE_CLIENT_ID}&redirect_uri={settings.GOOGLE_REDIRECT_URI}&scope=openid%20profile%20email&access_type=offline"
    }

# 구글이 리턴해준 params(code)를 쿼리에서 분리
@router.get("/login/oauth2/code/google")
async def auth_google(request: Request, response: Response, db: Session = Depends(get_db)):
    code = request.query_params.get('code')
    if not code:
        return RedirectResponse(url="https://ailogo.world:3000/google/error")
    
    token_url = "https://oauth2.googleapis.com/token"
    data = {
        "code": code,
        "client_id": settings.GOOGLE_CLIENT_ID,
        "client_secret": settings.GOOGLE_CLIENT_SECRET,
        "redirect_uri": settings.GOOGLE_REDIRECT_URI,
        "grant_type": "authorization_code"
    }
    # 구글 토큰 요청 
    token_response = requests.post(token_url, data=data)
    
    if token_response.status_code != 200:
        return {"error": "Failed to get access token", "details": token_response.text}
    
    # response로 받아온 구글 토큰
    token_json = token_response.json()
    access_token = token_json.get("access_token")
    refresh_token = token_json.get("refresh_token")
    
    if not access_token:
        return {"error": "No access token received", "details": token_json}
    
    # access_token을 활용해 로그인한 사용자 정보 받아오기
    user_info_response = requests.get(
        "https://www.googleapis.com/oauth2/v1/userinfo",
        headers={"Authorization": f"Bearer {access_token}"}
    )

    if user_info_response.status_code != 200:
        return {"error": "Failed to fetch user info", "details": user_info_response.text}
    # 구글측에서 받은 유저 정보
    user_info = user_info_response.json()
    
    # DB에서 user 조회
    db_user = get_user(db, user_info['email'])
    # 유저가 없는 경우 새로운 유저 생성
    if not db_user:
        db_user = create_google_user(db=db, user=user_info['email'])
    # 해당 아이디로 유저 정보 기입여부 확인
    db_user_info = get_user_info_db(db= db, user=user_info['email'] )
    type = "social"
    # 유저 정보를 기입했다면 role은 user
    if db_user_info:
        data = {"email": str(user_info['email']),"type":type,"role": db_user.role}
    # 아니라면 role은 guest로 제한적인 서비스 이용
    else:
        data = {"email": str(user_info['email']),"type":type, "role": db_user.role}
    
    # 로그인된 아이디 바탕으로 새롭게 jwt 토큰 생성
    access_token = jwt_service.create_access_token(data)
    refresh_token = jwt_service.create_refresh_token(data)
    
    # 쿠키 설정

    
    # 프론트로 리디렉션 응답 -> 쿼리에 필요 정보를 담아서 
    # 이렇게 하면 query에 토큰값이랑 이메일 정보가 노출되어 보안적으로는 redis에 이 값들을 저장하고
    # 프론트에서 redirect 될면서 바로 redis값을 찾는 요청을 보내 return 해주는게 더 안전한 방법이긴 함
    # 아래와 같이 보내는 경우에는 query 값으로 sessionStorage에 저장한 후 바로 메인페이지로 redirect 해야함
    
    redirect_url = f"https://ailogo.world/google/login?token={access_token}&role={db_user.role}&type={type}"
    response = RedirectResponse(url=redirect_url)
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=False,  # HTTPS 사용 시에만 True로 설정, 로컬 테스트라 False로 설정
        samesite='Lax',  # samesite는 'None', 'Lax', 'Strict' 중 하나여야 합니다. , 'Strict', 'None'은 HTTPS에서만 작동
        path="/"
    )
    return response

# 네이버 로그인
# 세부로직은 google과 동일
@router.get("/login/naver")
async def auth_naver_login():
    return {
            "url": f"https://nid.naver.com/oauth2.0/authorize?response_type=code&client_id={settings.NAVER_CLIENT_ID}&state=STATE_STRING&redirect_uri={settings.NAVER_CALLBACK_URI}&auth_type=reprompt"
    }

@router.get("/login/oauth2/code/naver")
async def auth_naver(request: Request, response: Response, db: Session = Depends(get_db)):
    code = request.query_params.get('code')
    state = request.query_params.get('state')
    if not code:
        return RedirectResponse(url="https://http://ailogo.world/google/error")
    
    token_url = "https://nid.naver.com/oauth2.0/token"
    data = {
        "code": code,
        "client_id": settings.NAVER_CLIENT_ID,
        "client_secret": settings.NAVER_CLIENT_SECRET,
        "redirect_uri": settings.NAVER_CALLBACK_URI,
        "grant_type": "authorization_code",
        "state": state
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
        "https://openapi.naver.com/v1/nid/me",
        headers={"Authorization": f"Bearer {access_token}"}
    )

    if user_info_response.status_code != 200:
        return {"error": "Failed to fetch user info", "details": user_info_response.text}
    
    user_info = user_info_response.json()
    db_user = get_user(db, user_info['response']['email'])
    if not db_user:
        db_user = create_google_user(db=db, user=user_info['response']['email'])
    db_user_info = get_user_info_db(db= db, user=user_info['response']['email'] )
    type = "social"
    if db_user_info:
        data = {"email": str(user_info['response']['email']),"type":type, "role": db_user.role}
    else:
        data = {"email": str(user_info['response']['email']),"type":type, "role": db_user.role}
    
    access_token = jwt_service.create_access_token(data)
    refresh_token = jwt_service.create_refresh_token(data)
    
    redirect_url = f"https://ailogo.world/naver/login?token={access_token}&role={db_user.role}&type={type}"
    response = RedirectResponse(url=redirect_url)
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=False,  # HTTPS 사용 시에만 True로 설정, 로컬 테스트라 False로 설정
        samesite='Lax',  # samesite는 'None', 'Lax', 'Strict' 중 하나여야 합니다. , 'Strict', 'None'은 HTTPS에서만 작동
        path="/"
    )
    return response
# 이메일 인증 보내는 로직(background로 멀티 스레드 작업을 통해 보내는 시간 단축)
@router.post("/send/email/code")
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

# 비밀번호 찾기에서 사용되는 이메일 인증 코드 
@router.post("/find/password/send/email/code")
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
@router.put("/check/code")
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
    # 비동기 작업을 통해 메일 보내는 시간 단축
    background_tasks.add_task(send_new_password, mail = mail.email,new_password=new_password)
    return HTTPException(status_code=status.HTTP_200_OK, detail="password change")

# 실제 이메일 전송 함수
async def send_email(**kwargs):
    mail = kwargs.get("mail", None)
    verification_code = kwargs.get("verification_code", None)
    email_pw = settings.EMAIL_PW
    email_addr = settings.EMAIL_ADDR
    try:
        yag = yagmail.SMTP({email_addr: "LoGO"}, email_pw)
        # https://myaccount.google.com/u/1/lesssecureapps
        with open('templates/smtp_template.html', 'r', encoding='utf-8') as file:
            html_template = file.read()
        html_content = html_template.format(verification_code=verification_code)
        contents = [html_content]
        yag.send(mail, '[LoGO]이메일 인증을 위한 인증번호를 안내 드립니다.', contents)
    except Exception as e:
        print(e)

# 새로운 비밀번호를 이메일로 보내는 함수        
async def send_new_password(**kwargs):
    mail = kwargs.get("mail", None)
    new_password = kwargs.get("new_password", None)
    email_pw = settings.EMAIL_PW
    email_addr = settings.EMAIL_ADDR
    try:
        yag = yagmail.SMTP({email_addr: "LoGO"}, email_pw)
        with open('templates/smtp_password_template.html', 'r', encoding='utf-8') as file:
            html_template = file.read()
        html_content = html_template.format(new_password=new_password)
        contents = [html_content]
        yag.send(mail, '[LoGO]새로운 비밀번호를 알려드립니다.', contents)
    except Exception as e:
        print(e)

# 로그아웃         
@router.post("/logout")
async def logout_user(request: Request, response: Response):
    # `refresh_token` 쿠키 삭제
    response.delete_cookie(key="refresh_token", path="/")  # domain과 path를 설정
    
    # 성공적으로 로그아웃되었음을 알리는 JSON 응답
    return {"message": "Logout successful"}


@router.post("/users/signup/admin")
def create_user(user: UserBase, db: Session = Depends(get_db)):
    create_admin(db=db, user=user)
    return HTTPException(status_code=200,detail="signup success")