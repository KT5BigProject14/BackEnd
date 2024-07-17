from fastapi import APIRouter
from api.routes import ai, login, news, redis, user_info, qna, redis

api_router = APIRouter()

# jwt_service = JWTService(JWTEncoder(),JWTDecoder(),settings.ALGORITHM,settings.SECRET_KEY,settings.ACCESS_TOKEN_EXPIRE_TIME,settings.REFRESH_TOKEN_EXPIRE_TIME)

# get_current_user = JWTAuthentication(jwt_service)

"retriever/news/"
api_router.include_router(login.router,prefix="/user", tags=["login"])
api_router.include_router(news.router, prefix="/news", tags=["news"])
api_router.include_router(redis.router, prefix="/redis", tags=["redis"])
api_router.include_router(
    user_info.router, prefix="/info", tags=["user_info"])
api_router.include_router(qna.router, prefix="/qna", tags=["qna"])

api_router.include_router(ai.router, prefix="/ai", tags=["ai"])
