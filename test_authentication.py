from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import HTMLResponse
from api.deps import JWTAuthentication
from typing import Annotated
from schemas import User, JwtUser
from sqlalchemy.orm import Session
from core.database import engine, get_db
from api.deps import JWTService
from schemas import JWTEncoder, JWTDecoder
from core.config import settings
from fastapi.testclient import TestClient
from main import app  # FastAPI 애플리케이션 인스턴스를 가져옵니다.
from core.config import settings
from schemas import JWTEncoder, JWTDecoder
router = APIRouter()
jwt_service = JWTService(JWTEncoder(),JWTDecoder(),settings.ALGORITHM,settings.SECRET_KEY,settings.ACCESS_TOKEN_EXPIRE_TIME,settings.REFRESH_TOKEN_EXPIRE_TIME)


# `TestClient` 인스턴스를 초기화합니다.
client = TestClient(app)

# 테스트 함수
def test_access_token_refresh():
    # 이곳에 유효하지 않은 액세스 토큰과 유효한 리프레시 토큰을 설정합니다.
    expired_access_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJlbWFpbCI6Im5hbWh5b25nMkBnbWFpbC5jb20iLCJ0eXBlIjoic29jaWFsIiwicm9sZSI6InVzZXIiLCJleHAiOjE3MjEyMzM3Njl9.HYdZ865raqIrOutD_7BkQpIWnnjDwPg0w1LMUsf9BXc"
    valid_refresh_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJlbWFpbCI6Im5hbWh5b25nMkBnbWFpbC5jb20iLCJ0eXBlIjoic29jaWFsIiwicm9sZSI6InVzZXIiLCJleHAiOjE3MjI0NDMzMDl9.lzYF7bOOLLRstwEqm1oXjcSPNH30uWV55OKK8OVn1xc"

    # 요청을 보내고 응답을 확인합니다.
    response = client.get(
        "/some-endpoint",
        headers={"Authorization": f"Bearer {expired_access_token}"},
        cookies={"refresh_token": valid_refresh_token}
    )

    # 상태 코드와 응답 헤더에서 새 액세스 토큰을 확인합니다.
    assert response.status_code == 401
    new_access_token = response.headers.get("new-access-token")
    assert new_access_token is not None
    print(f"New access token: {new_access_token}")
