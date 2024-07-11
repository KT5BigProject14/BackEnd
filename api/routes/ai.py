from fastapi import APIRouter, Depends, HTTPException, Request, BackgroundTasks, FastAPI
from fastapi.responses import HTMLResponse, JSONResponse, StreamingResponse
from api.deps import GetCurrentUser
from api.deps import JWTAuthentication
from typing import Annotated
from schemas import User, JwtUser
from sqlalchemy.orm import Session
from core.database import engine, get_db
from api.deps import JWTService
from schemas import JWTEncoder, JWTDecoder
from core.config import settings
import requests
import httpx
from typing import List
from models import Docs, SessionLocal
from pydantic import BaseModel


app = FastAPI()
router = APIRouter()
langserve_url = "http://localhost:8080/chain"


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# uvicorn main:app --reload

class TextRequest(BaseModel):
    title: str
    user_email: str


class TextResponse(BaseModel):
    text: str


@router.post("/chat")
async def chat(request: Request):
    try:
        # 요청 본문을 JSON 형식으로 파싱
        data = await request.json()
        session_id = data['session_id']
        user_email = data['user_email']
        question = data['question']

        # 모델 서버로 요청 보내기
        async with httpx.AsyncClient() as client:
            response = await client.post(
                langserve_url + "/chat",
                json={'user_email': user_email,
                      'session_id': session_id, 'question': question},
                timeout=None
            )

        response.raise_for_status()

        # 스트리밍 응답 처리
        async def iter_response():
            async for chunk in response.aiter_bytes():
                yield chunk

        return StreamingResponse(iter_response(), media_type="application/json")

    except httpx.RequestError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=e.response.status_code, detail=str(e))
    except KeyError as e:
        raise HTTPException(status_code=400, detail=f"Missing field: {e}")


@router.post("/title")
async def generate_search_title(request: Request):
    try:
        question = await request.json()

        # 첫 번째 서버로 요청 보내기
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{langserve_url}/generate/title", json={"request": question["question"]}, timeout=10.0
            )

        response.raise_for_status()

        # 응답에서 결과 파싱
        result = response.json()

        return {"question": question, "title": result}
    except requests.exceptions.RequestException as e:
        print(f"요청 예외: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        print(f"예외: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/text", response_model=TextResponse)
async def generate_search_text(request: Request, db: Session = Depends(get_db)):
    try:
        question = await request.json()

        # 첫 번째 서버로 요청 보내기
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{langserve_url}/generate/text", json={"title": question["title"]}, timeout=10.0
            )

        response.raise_for_status()

        # 랭서브로부터 결과 받기
        result = response.json()

        print("DB 저장 전 데이터:", question.user_email,
              question.title, result['response'])

        # db 저장
        new_doc = Docs(email=question.user_email,
                       title=question.title, content=result['response'])
        db.add(new_doc)
        db.commit()

        print("DB 저장 완료")

        return {"text": result['response']}
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=500, detail=f"Request failed: {e}")
    except Exception as e:
        db.rollback()  # 데이터베이스 변경 사항 롤백
        raise HTTPException(
            status_code=500, detail=f"An unexpected error occurred: {e}")
    finally:
        db.close()


# @router.post("/text")
# async def generate_search_text(request: Request, db: Session):
#     try:
#         data = await request.json()
#         user_email = data['user_email']
#         title = data['title']

#         # 랭서브로 요청 보내기
#         async with httpx.AsyncClient() as client:
#             response = await client.post(
#                 f"{langserve_url}/generate/text", json={"title": title}, timeout=10.0
#             )

#         result = response.json()

#         # db 저장
#         new_doc = Docs(email=user_email, title=title, content=result)
#         db.add(new_doc)
#         db.commit()

#         return {"text": result}
#     except requests.exceptions.RequestException as e:
#         raise HTTPException(status_code=500, detail=str(e))


# # input test 버전
# @router.post("/chat")
# async def chat(session_id: str, user_email: str, question: str):
#     try:
#         response = requests.post(
#             "http://localhost:8080/chain/chat", json={'user_email': user_email, 'session_id': session_id, 'question': question}
#         )
#         response.raise_for_status()

#         # 랭서브로부터 결과 받기
#         result = response.json()

#         return {"session_id": result['session_id'], "generated_chat": result["response"]}
#     except requests.exceptions.RequestException as e:
#         raise HTTPException(status_code=500, detail=str(e))


# # input test 버전
# @router.post("/title")
# async def generate_search_title(question: str):
#     try:
#         # 첫 번째 서버로 요청 보내기
#         response = requests.post(
#             "http://localhost:8080/chain/generate/title", json={"request": question}
#         )
#         response.raise_for_status()

#         # 응답에서 결과 파싱
#         result = response.json()

#         return {"question": question, "title": result}
#     except requests.exceptions.RequestException as e:
#         print(f"요청 예외: {e}")
#         raise HTTPException(status_code=500, detail=str(e))
#     except Exception as e:
#         print(f"예외: {e}")
#         raise HTTPException(status_code=500, detail=str(e))


# # input test 버전
# @router.post("/text", response_model=TextResponse)
# async def generate_search_text(request: TextRequest, db: Session = Depends(get_db)):
#     try:
#         # 랭서브로 요청 보내기
#         response = requests.post(
#             "http://localhost:8080/chain/generate/text", json={"title": request.title})
#         response.raise_for_status()

#         # 랭서브로부터 결과 받기
#         result = response.json()

#         print("DB 저장 전 데이터:", request.user_email,
#               request.title, result['response'])

#         # 결과 데이터 확인
#         if 'response' not in result:
#             raise HTTPException(
#                 status_code=500, detail="Invalid response format from the server")

#         # db 저장
#         new_doc = Docs(email=request.user_email,
#                        title=request.title, content=result['response'])
#         db.add(new_doc)
#         db.commit()

#         print("DB 저장 완료")

#         return {"text": result['response']}
#     except requests.exceptions.RequestException as e:
#         raise HTTPException(status_code=500, detail=f"Request failed: {e}")
#     except Exception as e:
#         db.rollback()  # 데이터베이스 변경 사항 롤백
#         raise HTTPException(
#             status_code=500, detail=f"An unexpected error occurred: {e}")
#     finally:
#         db.close()
