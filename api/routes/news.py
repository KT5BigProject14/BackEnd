from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import HTMLResponse

router = APIRouter()

# @router.post("/login/test-token", response_model=UserPublic)
# def test_token(current_user: CurrentUser) -> Any:
#     """
#     Test access token
#     """
#     return current_user