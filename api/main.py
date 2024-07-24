from fastapi import APIRouter
from api.routes import ai, login, redis, user_info, qna, redis,community

api_router = APIRouter()

api_router.include_router(login.router,prefix="/user", tags=["login"])
api_router.include_router(redis.router, prefix="/redis", tags=["redis"])
api_router.include_router(
    user_info.router, prefix="/info", tags=["user_info"])
api_router.include_router(qna.router, prefix="/qna", tags=["qna"])
api_router.include_router(community.router, prefix="/community", tags=["community"])

api_router.include_router(ai.router, prefix="/ai", tags=["ai"])
