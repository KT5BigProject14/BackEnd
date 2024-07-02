from fastapi import FastAPI, Depends, HTTPException, Response ,Request
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from typing import List
from models import Base, User as UserModel, UserInfo as UserInfoModel
from core.database import engine, get_db
from crud.login_crud import create_user_db, create_user_info_db, get_user, get_users, authenticate_user, email_auth, update_email_auth, create_email_auth\
    ,update_is_active
from schemas import User, UserCreate, UserInfo, UserInfoCreate, UserBase, JWTEncoder, JWTDecoder, SendEmail, MessageOk, CheckEmail, CheckCode
from typing import Annotated, Any
from fastapi import status
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.security import OAuth2PasswordRequestForm
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


# from models import MessageOk, SendEmail

# import boto3
# from botocore.exceptions import ClientError


router = APIRouter()
jwt_service = JWTService(JWTEncoder(),JWTDecoder(),settings.ALGORITHM,settings.SECRET_KEY,settings.ACCESS_TOKEN_EXPIRE_TIME,settings.REFRESH_TOKEN_EXPIRE_TIME)
# 함수 예시 
# @router.get,post중 선택("들어오는 url", response_model="schemas에 정의 된 json데이터의 구조 프론트로 return할 때 사용")
# def 기능에_맞는_함수_이름(변수: schema에_정의된_프론트에서_인풋으로_받은_json_구조, db: Session = Depends(get_db)):
#     # db 작업 부분으로 보내는 코드
#     return crud에서_선언한_함수이름(db=db, crud에_선언한_인자_이름=crud로_보낼_데이터(프론트에서 가져온 데이터))


# email, 이름, 비번
#회사명, 회사번호, 직책, 전화번호

@router.post("/users/signup")
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    db_user = get_user(db, user.email)
    if db_user:
        raise HTTPException(
            status_code=400, detail="User ID already registered")
    update_is_active(db,user)
    create_user_db(db=db, user=user)
    create_user_info_db(db= db, user_info = user)
    return HTTPException(status_code=200,detail="signup success")

@router.post("/users/login")
async def login_user(user: User, db: Session = Depends(get_db)):
    user_id  = authenticate_user(db=db, user=user)
    data = {"email":str(user_id.email)}
    access_token = jwt_service.create_access_token(data)
    refresh_token = jwt_service.create_refresh_token(data)
    response = JSONResponse(content={"detail":"login sucess"}, status_code=status.HTTP_200_OK)
    response.set_cookie(
        key="access_token", # 쿠키 이름
        value=access_token, # 쿠키 값
        httponly=True, # 자바스크립트 접근 불가능하게 하여 쿠키 조작 방지
        # secure=True, # https만 쿠키 전송
        samesite='none', # 모든 크로스 사이트에 대한 쿠기 사용 허가(프,백 분리 환경에서 일반적으로 사용)
    )
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        # secure=True,
        samesite='none',
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
        create_email_auth(db,mail,verification_code)
    return MessageOk()

@router.put("/email/check_code")
async def check_code(user_code: CheckCode, db: Session = Depends(get_db)):
    selected_email = email_auth(db,user_code)
    twenty_four_hours_ago = datetime.utcnow() - timedelta(hours=24)
    if selected_email.updated_at < twenty_four_hours_ago:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Verification code expired")
    elif selected_email.verify_number == user_code.verify_code:
        raise  HTTPException(status_code=status.HTTP_200_OK, detail="verify_code is same")
    else:
        raise  HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="verify_code is same")
        
    


email_content = """
<div id=":187" class="a3s aiL "><table border="0" cellpadding="0" cellspacing="0" style="width:815px;margin:55px auto;border:0;background-color:#fff;line-height:1.5;text-align:left;font-family:Roboto,Noto Sans KR,나눔고딕,NanumGothic,맑은고딕,Malgun Gothic,돋움,Dotum,Arial,Tahoma,Geneva,Verdana">
        <tbody><tr>
            <td style="padding-bottom:24px;border-bottom:2px solid #000">
                <a href="https://www.aihub.or.kr" title="새 창 열림" style="margin-left:6px" target="_blank" data-saferedirecturl="https://www.google.com/url?q=https://www.aihub.or.kr&amp;source=gmail&amp;ust=1719642303786000&amp;usg=AOvVaw2v2mG-E42S6-zrhCyl1Bjf">
                    <img src="https://ci3.googleusercontent.com/meips/ADKq_Nb2Wlc2ydv0_jaCHtDHR8iHexJ26ToSCSXotGz0FvrD1nV09dSXmLkUwHcDa8HiJgatLhsQbe7VFFiGJ5qm87g2kD8XnIiPF_k=s0-d-e1-ft#https://aihub.or.kr/static/image/mail/logoAIHub.png" alt="AI-Hub" style="border:0;vertical-align:top" class="CToWUd" data-bit="iit">
                </a>
            </td>
        </tr>
        <tr>
            <td style="height:24px"></td>
        </tr>
        <tr>
            <td>
                <a href="https://www.aihub.or.kr" title="새 창 열림" style="margin-left:6px" target="_blank" data-saferedirecturl="https://www.google.com/url?q=https://www.aihub.or.kr&amp;source=gmail&amp;ust=1719642303786000&amp;usg=AOvVaw2v2mG-E42S6-zrhCyl1Bjf"><img src="https://ci3.googleusercontent.com/meips/ADKq_NYalvzuOabIKI5J-vKzLaAlJFQaTv9YBy8SrQKMT7YI9euNCh0-lpuRexZInJ-tyEm4elQfwoJ-Ipe-uRsmyV4nNR0YdXSA=s0-d-e1-ft#https://aihub.or.kr/static/image/mail/imgHead.png" alt="" style="border:0;vertical-align:top" class="CToWUd" data-bit="iit"></a>
            </td>
        </tr>
        <tr>
            <td style="height:98px;font-size:22px;background-color:#f3f3f3;text-align:center;vertical-align:top">
                아래 <span class="il">인증</span><span class="il">번호</span>를 입력하시면 이메일 <span class="il">인증</span>이 완료됩니다.
            </td>
        </tr>
        <tr>
            <td style="height:50px"></td>
        </tr>
        <tr>
            <td style="padding:35px;border-top:1px solid #000;border-bottom:1px solid #cfd5d8;color:#666;font-size:15px;text-align:center;line-height:1.86">
                Retriever 회원가입 이메일 <span class="il">인증</span><span class="il">번호</span>입니다.<br>
                <span style="color:#000;font-size:20px;font-weight:500"><span class="il">인증</span><span class="il">번호</span> : </span>
                <span style="color:#378aff;font-size:20px;font-weight:500">{}</span><br><br>
                위 <span class="il">인증</span><span class="il">번호</span>는 이메일 <span class="il">인증</span>에 24시간 이내 1회 사용할 수 있습니다.<br>
                24시간이 경과된 후에는 다시 신청하셔야 합니다.<br><br>
                감사합니다.<br>
                - Retriever -
            </td>
        </tr>
        <tr>
            <td style="height:50px"></td>
        </tr>
        <tr>
            <td style="height:108px;vertical-align:top;text-align:center">
                <a href="https://www.aihub.or.kr" title="새 창 열림" target="_blank" data-saferedirecturl="https://www.google.com/url?q=https://www.aihub.or.kr&amp;source=gmail&amp;ust=1719642303786000&amp;usg=AOvVaw2v2mG-E42S6-zrhCyl1Bjf">
                    <img src="https://ci3.googleusercontent.com/meips/ADKq_NYWu82zKlCCGrk_PV3thGN6qeOso165IoiGK1LuCqgl8Uo5eoHgUJRhozwT3dfglzhrbdyMlGM2wmBc4o1HPBwCpZaDLR4t=s0-d-e1-ft#https://aihub.or.kr/static/image/mail/btnHome.png" alt="Retriever 홈페이지 바로가기" style="border:0;vertical-align:top" class="CToWUd" data-bit="iit">
                </a>
            </td>
        </tr>
        <tr>
            <td style="height:126px;font-size:16px;vertical-align:middle;text-align:center;line-height:28px;background-color:#f5f5f5">
                본 메일은 회원님께서 Retriever 이메일 수신동의를 하였기에 발송되었습니다.<br>
                메일 수신을 원치 않으시면 <a title="새 창 열림" style="color:#378aff;text-decoration:underline">[회원정보 관리]</a> 메뉴에서 수신 여부를 수정해주시기 바랍니다.
            </td>
        </tr>
        <tr>
            <td style="height:104px;color:#fff;font-size:16px;font-weight:300;vertical-align:middle;text-align:center;line-height:28px;background-color:#424242">
                CONTACT : Retriever : RetrieverKr<br>
                전화 : 02-1234-1234 / 이메일 : <a href="mailto:aihub@aihub.kr" target="_blank">aihub@aihub.kr</a>
            </td>
        </tr>
    </tbody></table>
<table style="display:none"><tbody><tr><td><img src="https://ci3.googleusercontent.com/meips/ADKq_NZcK-CwqcsMJuaxGx5HCGRksI3QzS-sPZvEs2sXvBhqhDNsT1eKkpknOKSzuVb9k4YBURT7tri-bMsCggAXq8dVgVGcGAB2jxv7p1DhKlxjkiO46Id8WV0uoDcsIWHF2FVyqLzkYkKGagFvrk9hhVRo_kR0Dg91oB5ssQxoErLlTwcHtKrndM_o36QqMjqjnsBpvl3eLVR5_74Y0dckjuLJjKXCokfChwH0tSRiOtEUEkKgqRfgCZNSOjNNPc73lF6AIBO3IJuYP8RnLLBAPP4VSw=s0-d-e1-ft#https://kr1-mail.worksmobile.com/readReceipt/notify/?img=SfKwKAgmKAu%2FFAglKqg9FAbshAuZaxMdaxuXFA25Kqt%2FFL%2FwFqudFouqaAv%2FKxUltzJG1HkS76CTW6kXMBKmKAuQarlCW6ClWrlNKvINW6JGWVloWrd%3D.gif" border="0" class="CToWUd" data-bit="iit"></td></tr></tbody></table></div>
"""

async def send_email(**kwargs):
    mail = kwargs.get("mail", None)
    verification_code = kwargs.get("verification_code", None)
    email_pw = settings.EMAIL_PW
    email_addr = settings.EMAIL_ADDR
    try:
        yag = yagmail.SMTP({email_addr: "Retriever"}, email_pw)
        # https://myaccount.google.com/u/1/lesssecureapps
        # 추후에 html 파일로 바꿈
        contents = [
            email_content.format(verification_code)
        ]
        yag.send(mail, '[Retriever]이메일 인증을 위한 인증번호를 안내 드립니다.', contents)
    except Exception as e:
        print(e)

@router.post("/users/loout")
async def logout_user(response: Response, request: Request):
    access_token = request.cookies.get("access_token")
    refresh_token = request.cookies.get("refresh_token")
    response.delete_cookie(key="access_token")
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


@router.post("/user_info/", response_model=UserInfo)
def create_user_info(user_info: UserInfoCreate, db: Session = Depends(get_db)):
    db_user = get_user(db, user_info.email)
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return create_user_info_db(db=db, user_info=user_info)


@router.get("/user_info/{email}", response_model=UserInfo)
def read_user_info(email: str, db: Session = Depends(get_db)):
    db_user_info = db.query(UserInfoModel).filter(
        UserInfoModel.email == email).first()
    if db_user_info is None:
        raise HTTPException(status_code=404, detail="User Info not found")
    return db_user_info
    