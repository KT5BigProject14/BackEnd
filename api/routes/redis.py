from fastapi import FastAPI, APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import List
import requests
import httpx

app = FastAPI()
router = APIRouter()
langserve_url = "http://localhost:8080/redis"


class all_messagesResponse(BaseModel):
    messages: List[str]


@app.get("/all_messages", response_model=all_messagesResponse)
async def get_all_messages_for_user(user_email: str = Query(..., description="The email of the user to get messages for")):
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(
                f"{langserve_url}/all_messages", params={"user_email": user_email}
            )
            response.raise_for_status()
            result = await response.json()
            return all_messagesResponse(messages=result.get('messages', []))
        except httpx.RequestError as e:
            print(f"Request error: {e}")
            raise HTTPException(status_code=500, detail=str(e))
        except httpx.HTTPStatusError as e:
            print(f"HTTP status error: {e.response.status_code}")
            raise HTTPException(
                status_code=e.response.status_code, detail=e.response.text)
        except Exception as e:
            print(f"Unexpected error: {e}")
            raise HTTPException(status_code=500, detail=str(e))


# @router.get("/all_messages", response_model=all_messagesResponse)
# async def get_all_messages_for_user(user_email: str):
#     async with httpx.AsyncClient() as client:
#         try:
#             response = await client.get(
#                 f"{langserve_url}/all_messages", params={"user_email": user_email}
#             )
#             response.raise_for_status()
#             result = response.json()  # await 추가
#             return all_messagesResponse(messages=result.get('messages', []))
#         except httpx.RequestError as e:
#             print(f"요청 예외: {e}")
#             raise HTTPException(status_code=500, detail=str(e))
#         except Exception as e:
#             print(f"예외: {e}")
#             raise HTTPException(status_code=500, detail=str(e))
