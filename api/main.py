from fastapi import APIRouter

from api.routes import login,news,redis
api_router = APIRouter()
api_router.include_router(login.router, tags=["login"])
api_router.include_router(news.router, prefix="/news", tags=["news"])
api_router.include_router(redis.router, prefix="/redis", tags=["redis"])
