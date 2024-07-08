from fastapi import APIRouter, UploadFile, File, HTTPException, Request
from .RAGPipeLine import Ragpipeline
# from fastapi.responses import JSONResponse

router = APIRouter()

# RAGPipeline 초기화
ragpipe = Ragpipeline()


def get_rag_pipeline():
    return ragpipe


@router.get("/rag_pipeline_endpoint")
async def rag_pipeline_example():
    return {"message": "RAG Pipeline Endpoint"}


@router.post("/chat")
async def chat(question: str, session_id: str, user_email: str):
    try:
        ragpipe.current_user_email = user_email
        ragpipe.current_session_id = session_id
        response = ragpipe.chat_generation(question)
        return {"response": response}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/update-vector-db")
async def update_vector_db(file: UploadFile = File(...)):
    try:
        filename = file.filename
        file_content = await file.read()
        success = ragpipe.update_vector_db(file_content, filename)
        if success:
            return {"status": "success", "message": "Vector store updated successfully."}
        else:
            return {"status": "failed", "message": "Document was too similar to existing entries."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/delete-vector-db")
async def delete_vector_db(doc_id: str):
    try:
        ragpipe.delete_vector_db_by_doc_id(doc_id)
        return {"status": "success", "message": f"Document with ID {doc_id} deleted successfully."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# @router.post("/chain/stream_log")
# async def stream_log(request: Request):
#     try:
#         body = await request.json()
#         input_data = body['input']
#         question = input_data.get('input')
#         response = ragpipe.chat_generation(question=question)
#         return JSONResponse(content=response)
#     except Exception as e:
#         raise HTTPException(status_code=422, detail=str(e))
