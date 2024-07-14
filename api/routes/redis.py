from fastapi import FastAPI, APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import List
import requests
import httpx
from datetime import datetime
import re

app = FastAPI()
router = APIRouter()
langserve_url = "http://localhost:8080/redis"


class all_messagesResponse(BaseModel):
    messages: List[str]


# 메시지를 정리하고 저장하는 함수
def extract_and_sort_messages(messages):
    # 숫자가 아닌 메시지 추출
    messages = [msg for msg in messages if not msg.isdigit()]

    # 메시지에서 시간과 내용을 분리하여 리스트로 저장
    messages_with_time = []
    for msg in messages:
        match = re.match(
            r'(\d{4}\.\d{2}\.\d{2} \d{2}:\d{2}:\d{2}) - (.+)', msg)
        if match:
            time_str = match.group(1)
            message_text = match.group(2)
            messages_with_time.append([time_str, message_text])

    # 시간순으로 정렬
    sorted_messages = sorted(
        messages_with_time, key=lambda x: datetime.strptime(x[0], '%Y.%m.%d %H:%M:%S'))

    # 정렬된 결과를 단순 리스트 형태로 변환
    result = []
    for message in sorted_messages:
        result.extend(message)  # 시간을 리스트에 추가

    return result


@router.get("/all_messages", response_model=all_messagesResponse)
async def get_all_messages_for_user(user_email: str = Query(..., description="The email of the user to get messages for")):
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(
                f"{langserve_url}/all_messages", params={"user_email": user_email}
            )
            response.raise_for_status()
            result = response.json()
            result = extract_and_sort_messages(result.get('messages', []))

            return {"messages": result}
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


@router.get("/messages/{user_email}/{session_id}")
async def get_messages_for_user(user_email: str, session_id: str, start: int = 0, end: int = -1):
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{langserve_url}/messages/{user_email}/{session_id}",
                params={"start": start, "end": end},
                timeout=10.0
            )
            response.raise_for_status()
            messages = response.json()
            return messages
    except httpx.RequestError as e:
        raise HTTPException(status_code=500, detail=f"Request error: {e}")
    except httpx.HTTPStatusError as e:
        raise HTTPException(
            status_code=e.response.status_code, detail=e.response.text)
