from fastapi import APIRouter

from api.routes import login,news
api_router = APIRouter()
api_router.include_router(login.router, tags=["login"])
api_router.include_router(news.router, prefix="/news", tags=["news"])
