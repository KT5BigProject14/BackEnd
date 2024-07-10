from fastapi import FastAPI, APIRouter, HTTPException
from pydantic import BaseModel
from typing import List
import requests
import httpx

router = APIRouter()
langserve_url = "http://localhost:8080/redis"


class all_messagesResponse(BaseModel):
    messages: List[str]


@router.get("/all_messages", response_model=all_messagesResponse)
async def get_all_messages_for_user(user_email: str):
    try:
        response = requests.get(
            f"{langserve_url}/all_messages", params={"user_email": user_email}
        )
        response.raise_for_status()
        result = response.json()
        return all_messagesResponse(messages=result.get('messages', []))
    except requests.exceptions.RequestException as e:
        print(f"요청 예외: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        print(f"예외: {e}")
        raise HTTPException(status_code=500, detail=str(e))
