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


app = FastAPI()
router = APIRouter()
langserve_url = "http://localhost:8080/chain"

# uvicorn main:app --reload


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
        # response = requests.post(
        #     langserve_url+"/generate/title", json={"request": question["question"]}
        # )
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


@router.post("/text")
async def generate_search_text(request: Request):
    try:
        data = await request.json()
        user_email = data['user_email']
        title = data['title']

        # 랭서브로 요청 보내기
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{langserve_url}/generate/text", json={"title": title}, timeout=10.0
            )

        # # 랭서브로 요청 보내기
        # response = requests.post(
        #     langserve_url + "/generate/text", json={"title": title})
        # response.raise_for_status()

        # 랭서브로부터 결과 받기
        result = response.json()

        return {"text": result}
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=500, detail=str(e))


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
# @router.post("/text")
# async def generate_search_text(title: str):
#     try:
#         # 랭서브로 요청 보내기
#         response = requests.post(
#             "http://localhost:8080/chain/generate/text", json={"title": title})
#         response.raise_for_status()

#         # 랭서브로부터 결과 받기
#         result = response.json()

#         return {"text": result}
#     except requests.exceptions.RequestException as e:
#         raise HTTPException(status_code=500, detail=str(e))

# def get_db():
#     db = SessionLocal()
#     try:
#         yield db
#     finally:
#         db.close()


# async def fetch_titles_from_model(question: str) -> List[str]:
#     async with httpx.AsyncClient() as client:
#         response = await client.post(langserve_url+"/generate/title", json={"request": question})
#         response.raise_for_status()
#         return response.json()["titles"]


# async def fetch_texts_from_model(titles: List[str]) -> List[str]:
#     async with httpx.AsyncClient() as client:
#         response = await client.post(langserve_url + "/generate/text", json={"titles": titles})
#         response.raise_for_status()
#         return response.json()["texts"]


# @router.post("/title")
# async def generate_search_title(question: str, email: str, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
#     try:
#         # 모델 백엔드로 타이틀 생성 요청 보내기
#         titles = await fetch_titles_from_model(question)

#         # 백그라운드 작업으로 텍스트 생성 및 출력 요청
#         background_tasks.add_task(
#             generate_texts_and_save, titles, question, email, db)

#         # 타이틀을 프론트엔드에 반환
#         print(titles)
#         return {"titles": titles}
#     except httpx.RequestError as e:
#         print(f"요청 예외: {e}")
#         raise HTTPException(status_code=500, detail=str(e))
#     except Exception as e:
#         print(f"예외: {e}")
#         raise HTTPException(status_code=500, detail=str(e))


# async def generate_texts_and_save(titles: str, question: str, email: str, db: Session):
#     try:
#         texts = await fetch_texts_from_model({"titles": titles})
#         # 생성된 텍스트를 콘솔에 출력
#         new_doc = Docs(email=email, question=question, docs=texts)
#         db.add(new_doc)
#         db.commit()
#         print(f"Generated texts: {texts}")
#     except httpx.RequestError as e:
#         print(f"요청 예외: {e}")
#     except Exception as e:
#         print(f"예외: {e}")
