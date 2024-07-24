from fastapi import APIRouter, Depends, HTTPException, Request, BackgroundTasks, FastAPI
from fastapi.responses import JSONResponse, StreamingResponse
from sqlalchemy.orm import Session
from core.database import engine, get_db
from models import Docs, SessionLocal
from core.config import settings
import httpx
import uuid
from typing import Optional
from starlette.requests import Request as Requests
from pydantic import BaseModel
from core.config import settings
app = FastAPI()
router = APIRouter()
langserve_url = settings.LANGSERVE_URL

# Pydantic 모델들
class TitleRequest(BaseModel):
    question: str

class TitleResponse(BaseModel):
    question: str
    title: str

class TextRequest(BaseModel):
    title: str

class TextResponse(BaseModel):
    docs_id: int
    text: str

class ChatRequest(BaseModel):
    session_id: Optional[str]
    question: str

class DocsSaveRequest(BaseModel):
    docs_id: int

class GetTextRequest(BaseModel):
    docs_id: int

# 채팅 엔드포인트
@router.post("/chat")
async def chat(request: Requests, chat_request: ChatRequest):
    try:
        user = request.state.user
        session_id = chat_request.session_id or str(uuid.uuid4())
        user_email = user.email
        question = chat_request.question

        # 모델 서버로 요청 보내기
        async with httpx.AsyncClient() as client:
            response = await client.post(
                langserve_url + "/chain/chat",
                json={'user_email': user_email,
                      'session_id': session_id,
                      'question': question},
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

# 제목 생성 엔드포인트
@router.post("/title")
async def generate_search_title(title_request: TitleRequest):
    try:
        # 첫 번째 서버로 요청 보내기
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{langserve_url}/chain/generate/title", json={"request": title_request.question}
            )

        response.raise_for_status()

        # 응답에서 결과 파싱
        result = response.json()['response']

        # Split the text into individual lines
        lines = result.split('\n')

        # Extract the quoted sentences and store them in a list
        title = [line.split('\"')[0] for line in lines]

        return {"question": title_request.question, "title": title}
    except httpx.RequestError as e:
        raise HTTPException(status_code=500, detail=f"Request failed: {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {e}")

# 텍스트 생성 엔드포인트
@router.post("/text", response_model=TextResponse)
async def generate_search_text(request: Requests, text_request: TextRequest, db: Session = Depends(get_db)):
    try:
        user = request.state.user
        # 랭서브로 요청 보내기
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{langserve_url}/chain/generate/text", json={"title": text_request.title}
            )

        response.raise_for_status()

        # 랭서브로부터 결과 받기
        result = response.json()

        print("DB 저장 전 데이터:", user.email, text_request.title, result['response'])

        # 결과 데이터 확인
        if 'response' not in result:
            raise HTTPException(status_code=500, detail="Invalid response format from the server")

        # db 저장
        new_doc = Docs(email=user.email, title=text_request.title, content=result['response'])
        db.add(new_doc)
        db.commit()
        db.refresh(new_doc)  # 새로 추가된 문서의 ID를 가져오기 위해 refresh

        print("DB 저장 완료")

        # docs_id 포함하여 반환
        return {"docs_id": new_doc.docs_id, "text": result['response']}
    except httpx.RequestError as e:
        raise HTTPException(status_code=500, detail=f"Request failed: {e}")

# 좋아요 저장 엔드포인트
@router.post("/like")
async def docs_save(docs_save_request: DocsSaveRequest, db: Session = Depends(get_db)):
    try:
        # 해당 문서를 찾습니다.
        doc = db.query(Docs).filter(Docs.docs_id == docs_save_request.docs_id).one()

        # is_like 값을 반대로 바꿉니다. 0: 싫어요, 1: 좋아요
        doc.is_like = not doc.is_like

        # 변경 사항을 커밋합니다.
        db.commit()

        return {"is_like": doc.is_like}
    except httpx.RequestError as e:
        raise HTTPException(status_code=500, detail=f"Request failed: {e}")
    except Exception as e:
        db.rollback()  # 데이터베이스 변경 사항 롤백
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {e}")
    finally:
        db.close()

# 모든 제목 가져오기 엔드포인트
@router.get("/view/all/title")
async def get_all_title_for_user(request: Requests, db: Session = Depends(get_db)):
    try:
        user = request.state.user

        # 해당 문서를 찾습니다.
        docs = db.query(Docs).filter(Docs.email == user.email).order_by(Docs.created_at.desc()).all()

        if not docs:
            raise HTTPException(status_code=404, detail="Document not found")

        # 문서의 title, docs_id, created_at을 추출하여 리스트로 반환합니다.
        result = [
            {
                "docs_id": doc.docs_id,
                "title": doc.title,
                "time": doc.created_at
            }
            for doc in docs
        ]

        return {"documents": result}
    except httpx.RequestError as e:
        raise HTTPException(status_code=500, detail=f"Request failed: {e}")
    except Exception as e:
        db.rollback()  # 데이터베이스 변경 사항 롤백
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {e}")
    finally:
        db.close()

# 특정 텍스트 가져오기 엔드포인트
@router.get("/view/text/{docs_id}")
async def get_text_for_user(docs_id: int, db: Session = Depends(get_db)):
    try:
        # 해당 문서를 찾습니다.
        doc = db.query(Docs).filter(Docs.docs_id == docs_id).one()

        text = doc.content

        return {"text": text}
    except httpx.RequestError as e:
        raise HTTPException(status_code=500, detail=f"Request failed: {e}")
    except Exception as e:
        db.rollback()  # 데이터베이스 변경 사항 롤백
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {e}")
    finally:
        db.close()

# 모든 좋아요 누른텍스트 가져오기 엔드포인트
@router.get("/get/like/text")
async def get_all_text_for_user(request: Requests, db: Session = Depends(get_db)):
    try:
        user = request.state.user

        # 해당 문서를 찾습니다.
        docs = db.query(Docs).filter(Docs.email == user.email, Docs.is_like == True).order_by(Docs.created_at.desc()).all()

        if not docs:
            raise HTTPException(status_code=404, detail="Document not found")

        # 문서의 title, docs_id, created_at을 추출하여 리스트로 반환합니다.
        result = [
            {
                "docs_id": doc.docs_id,
                "title": doc.title,
                "text": doc.content,
                "time": doc.created_at
            }
            for doc in docs
        ]

        return {"documents": result}
    except httpx.RequestError as e:
        raise HTTPException(status_code=500, detail=f"Request failed: {e}")
    except Exception as e:
        db.rollback()  # 데이터베이스 변경 사항 롤백
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {e}")
    finally:
        db.close()

app.include_router(router, prefix="/retriever/ai")
