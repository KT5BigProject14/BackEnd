from fastapi import FastAPI, HTTPException, APIRouter
from pydantic import BaseModel
from core.redis_config import redis_conn
import uuid

router = APIRouter()

class Message(BaseModel):
    user_email: str
    session_id: str
    message: str

# 유저의 대화내용 저장
@router.post("/save_message/")
async def save_message(msg: Message):
    #처음 대화인 경우
    if msg.session_id:
        save_message(msg.user_email, msg.session_id, msg.message)    
    #이전 대화가 있는 경우
    else:
        session_id = str(uuid.uuid4())
        save_message(msg.user_email, session_id, msg.message)
    return {"status": "Message saved"}


# 특정 유저의 특정 session에 대한 대화 불러오기 
@router.get("/messages/{user_email}/{session_id}")
async def get_messages_for_user(user_email: str, session_id: str, start: int = 0, end: int = -1):
    messages = get_messages(user_email, session_id, start, end)
    if not messages:
        raise HTTPException(status_code=404, detail="No messages found")
    return {"messages": messages}


# 특정 유저의 모든 대화 세션 불러오기
@router.get("/all_messages/{user_email}")
async def get_all_messages_for_user_endpoint(user_email: str):
    messages = scan_keys(user_email)
    
    return messages

@router.delete("/del_message")
async def delete_message(user_email: str, session_id: str):
    return_value = del_message(user_email,session_id)
    if return_value:
        return HTTPException(status_code=200, detail="delete session")

# 유저의 sessionid가 키로 있으면 해당키에 대화 저장, 없다면 새로 키를 만들어서 저장
def save_message(user_email: str, session_id: str, message: str):
    key = f"user:{user_email}:session:{session_id}:messages"
    redis_conn.lpush(key, message)  # 대화 내용을 리스트의 앞에 추가

# 특정 유저의 특정 session_id의 모든 대화내용 조회
def get_messages(user_email: str, session_id: str, start: int = 0, end: int = -1):
    key = f"user:{user_email}:session:{session_id}:messages"
    messages = redis_conn.lrange(key, start, end)  # 대화 내용을 조회
    return [msg.decode('utf-8') for msg in messages]

# 특정 유저의 모든 대화 세션 불러오기
def scan_keys(user_email: str):
    pattern = f"user:{user_email}:*"
    cursor = '0'
    # 키를 분리 => for문을 돌려서 session_id를 분리 하면서 -> 키로 대화 마지막 내용을 조회하고 
    # -> {sessiond_id : 대화의 마지막 내용}으로 구성하여 리스트에 push 하면 for문 한사이클 끝
    # for문이 완료되면, json으로 response 해줘야 함 
    keys = []
    while cursor != 0:
        cursor, new_keys = redis_conn.scan(cursor=cursor, match=pattern)
        keys.extend(new_keys)
    messages = []
    for key in keys:
        # 문자열을 ':'로 분리
        key = key.decode('utf-8')
        parts = key.split(':')
        # session_id는 네 번째 요소에 위치
        session_id = parts[3]
        message = redis_conn.lrange(key,-2,-2)
        messages.append({session_id:message[0].decode('utf-8')})
        
    return messages

def del_message(user_email: str, session_id : str):
    key = f"user:{user_email}:session:{session_id}:messages"
    redis_conn.delete(key)
    return True