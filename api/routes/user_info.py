from fastapi import APIRouter, Depends, HTTPException, status, Response
from sqlalchemy.orm import Session
from models import UserInfo
from core.database import engine, get_db
from crud.login_crud import authenticate_user, update_password
from crud.info_crud import update_user_info_db, get_user_info_db, create_user_info_db, change_user_role
from schemas import UserInfoBase, User
from fastapi import Security
from fastapi.security import OAuth2PasswordBearer
from starlette.background import BackgroundTasks
from schemas import SendEmail, MessageOk, ChangePassword, JWTEncoder, JWTDecoder
import secrets
import yagmail
from crud.login_crud import email_auth, update_email_auth
from core.config import settings
from api.deps import JWTService
from fastapi.responses import JSONResponse
from starlette.requests import Request


router = APIRouter()
jwt_service = JWTService(JWTEncoder(),JWTDecoder(),settings.ALGORITHM,settings.SECRET_KEY,settings.ACCESS_TOKEN_EXPIRE_TIME,settings.REFRESH_TOKEN_EXPIRE_TIME)

# request에 담겨있는 토큰 파싱한 유저 정보로 email 찾음
@router.get("/user")
def read_user_info(request: Request, db: Session = Depends(get_db) ):
    print(request)
    user = request.state.user
    print(user.email)
    db_user_info = get_user_info_db(db = db,user= user.email )
    if db_user_info is None:
        raise HTTPException(status_code=404, detail="User Info not found")
    return db_user_info

@router.post("/create/user")
def create_user_info(request:Request, response: Response, user_info: UserInfoBase, db: Session = Depends(get_db)):
    user = request.state.user
    user_info = create_user_info_db(db =db, user_info =user_info, email = user.email)
    user = change_user_role(db = db, user = user_info.email)
    response.delete_cookie(key="refresh_token")
    data = {"email": str(user.email), "name": user_info.user_name, "role": user.role }
    access_token = jwt_service.create_access_token(data)
    refresh_token = jwt_service.create_refresh_token(data)
    response = JSONResponse(content={"access_token":access_token,"user_name":str(user_info.user_name), "role": user.role}, status_code=status.HTTP_200_OK)
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=False,
        samesite='lax',
        path="/"
    )
    return response

@router.put("/change/user")
def update_user_info(request: Request, user_info: UserInfoBase ,db: Session = Depends(get_db)):
    user = request.state.user
    update_user_info_db(db, user_info, user.email)
    return HTTPException(status_code=200, detail="update_user_info")

@router.post("/change/password")
async def email_by_gmail(request:Request, password:ChangePassword ,db: Session = Depends(get_db)):
    user = request.state.user
    type = request.state.type

    if type == "social":
        raise HTTPException(status_code=status.HTTP_406_NOT_ACCEPTABLE, detail="Social logins cannot change passwords.")
    check_user = User(email=user.email, password=password.password)
    confirm_password = authenticate_user(db, check_user)
    if confirm_password:
        update_password(db, password,email=user.email)
    return HTTPException(status_code=status.HTTP_200_OK, detail="change password successful")
