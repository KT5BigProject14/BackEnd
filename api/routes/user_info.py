from fastapi import APIRouter, Depends, HTTPException, status, Response
from sqlalchemy.orm import Session
from models import UserInfo
from core.database import engine, get_db
from crud.login_crud import authenticate_user, update_password
from crud.info_crud import update_user_info_db, get_user_info_db, create_user_info_db, change_user_role, create_keyword_db, get_user_keyword, update_keyword_db
from schemas import UserInfoBase, User
from fastapi import Security
from fastapi.security import OAuth2PasswordBearer
from starlette.background import BackgroundTasks
from schemas import SendEmail, MessageOk, ChangePassword, JWTEncoder, JWTDecoder ,Keywords
import secrets
import yagmail
from crud.login_crud import email_auth, update_email_auth
from core.config import settings
from api.deps import JWTService
from fastapi.responses import JSONResponse
from starlette.requests import Request


router = APIRouter()
jwt_service = JWTService(JWTEncoder(),JWTDecoder(),settings.ALGORITHM,settings.SECRET_KEY,settings.ACCESS_TOKEN_EXPIRE_TIME,settings.REFRESH_TOKEN_EXPIRE_TIME)

# request에 담겨있는 토큰 디코딩한 유저 정보로 email 찾음
@router.get("/user")
def read_user_info(request: Request, db: Session = Depends(get_db)):
    user = request.state.user
    # 유저 정보 db 조회
    db_user_info = get_user_info_db(db=db, user=user.email)
    if db_user_info is None:
        raise HTTPException(status_code=404, detail="User Info not found")
    # keyword 테이블 조회
    db_user_keyword = get_user_keyword(email=user.email, db=db)
    
    return {
        "user_info": db_user_info,
        "user_keyword": db_user_keyword
    }

# 유저 정보 생성
@router.post("/create/user")
def create_user_info(request:Request, response: Response, user_info: UserInfoBase, db: Session = Depends(get_db)):
    user = request.state.user
    user_info = create_user_info_db(db =db, user_info =user_info, email = user.email)
    # 처음 유저 정보가 생성되면 guest에서 user로 role이 바뀜
    user = change_user_role(db = db, user = user_info.email)
    # 바뀐 유저 정보로 인해 새로운 쿠키를 넣어주기 위해 기존 guest로 만들어진 jwt 토큰의 refresh 토큰 삭제
    response.delete_cookie(key="refresh_token")
    data = {"email": str(user.email), "name": user_info.user_name, "role": user.role }
    # 새로운 토큰 발급
    access_token = jwt_service.create_access_token(data)
    refresh_token = jwt_service.create_refresh_token(data)
    # 새로운 access_token return
    response = JSONResponse(content={"access_token":access_token,"user_name":str(user_info.user_name), "role": user.role}, status_code=status.HTTP_200_OK)
    # 새로운 refresh_token set
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=False,
        samesite='lax',
        path="/"
    )
    return response
# 유저 정보 변경
@router.put("/change/user")
def update_user_info(request: Request, user_info: UserInfoBase ,db: Session = Depends(get_db)):
    user = request.state.user
    update_user_info_db(db, user_info, user.email)
    return HTTPException(status_code=200, detail="update_user_info")

# 비밀번호 변경
@router.post("/change/password")
async def email_by_gmail(request:Request, password:ChangePassword ,db: Session = Depends(get_db)):
    user = request.state.user
    type = request.state.type
    
    # 소셜 로그인은 비밀번호 없기 때문에 exception
    if type == "social":
        raise HTTPException(status_code=status.HTTP_406_NOT_ACCEPTABLE, detail="Social logins cannot change passwords.")
    check_user = User(email=user.email, password=password.password)
    # 기존 유저의 비밀번호왜 유저가 확인용으로 넣은 비밀번호가 같은지 확인
    confirm_password = authenticate_user(db, check_user)
    # 위 결과과 True라면 새롭게 입력한 비밀번호로 update
    if confirm_password:
        update_password(db, password,email=user.email)
    return HTTPException(status_code=status.HTTP_200_OK, detail="change password successful")

# 유저 keyword 정보 조히
@router.get("/keyword")
def read_keyword(request: Request, db: Session = Depends(get_db)):
    user = request.state.user
    db_user_keyword = get_user_keyword(email=user.email, db=db)
    return db_user_keyword

# 유저 keyword 정보 변경 혹은 삽입
@router.post("/keyword")
async def post_keyword(request:Request, keyword: Keywords, db: Session = Depends(get_db)):
    # db에 기존에 입력한 keyword가 있는지 확인
    db_user_keyword = get_user_keyword(request.state.user.email, db =db)
    # 있다면 새롭게 업데이트 
    if db_user_keyword:
        update_keyword_db(keyword=keyword,email = request.state.user.email, db =db)
    # 없다면 새로 삽입
    else:
        create_keyword_db(keyword=keyword,email = request.state.user.email, db =db)