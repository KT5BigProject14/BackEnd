from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from models import UserInfo
from core.database import engine, get_db
from crud.info_crud import update_user_info_db, get_user_info_db, create_user_info_db
from schemas import UserInfoBase, User
from fastapi import Security, Request
from fastapi.security import OAuth2PasswordBearer
router = APIRouter()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/retriever/users/login")
def verify_header(token: str = Depends(oauth2_scheme)) -> str:
    # Bearer token을 받는 부분
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Bearer token is missing",
            headers={"WWW-Authenticate": "Bearer"},
        )
    # 추가적인 토큰 검증 로직이 여기에 들어갈 수 있습니다.
    return token

# request에 담겨있는 토큰 파싱한 유저 정보로 email 찾음
@router.get("/user_info")
def read_user_info(request: Request, db: Session = Depends(get_db), token: str = Depends(verify_header)):
    print(request.state.user)
    db_user_info = get_user_info_db(db = db,user= request.state.user.email )
    if db_user_info is None:
        raise HTTPException(status_code=404, detail="User Info not found")
    return db_user_info

@router.post("/create/user_info")
def create_user_info(user_info: UserInfoBase, db: Session = Depends(get_db)):
    user_info = create_user_info_db(db =db, user_info =user_info)
    return HTTPException(status_code=200, detail="create user info")

@router.put("/user_info/")
def update_user_info(user_info: UserInfoBase ,db: Session = Depends(get_db), token: str = Depends(verify_header)):
    update_user_info_db(db, user_info)
    return HTTPException(status_code=200, detail="update_user_info")
    