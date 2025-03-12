from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from core.config import settings

# db 엔진 생성
engine = create_engine(
    settings.SQLALCHEMY_DATABASE_URL,
    pool_size=20,  # 기본 연결 풀 크기
    max_overflow=30,  # 오버플로우 한계
    pool_timeout=30,  # 연결 시도 타임아웃 (초)
    pool_recycle=3600,  # 연결 재활용 시간 (초)
)

# 세션 로컬설정
# autocommit = False : 자동 커밋 비활성화 -> 명시적으로 트랜젝션 커밋해야 함
# autoflush = False : 자동 플러시 비활성화 -> 변경사항을 데이터베이스에 반영하기 위해 명시적으로 flush
# bind = engine : 생성된 엔진을 세션에 바인딩 -> 세션을 통해 데이터베이스 연결 사용 가능
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 새로운 데이터 베이스 세션 생성
# yield에서 새롭게 생성된 세션을 반환하고
# finally에서 세션을 닫아 데이터 베이스를 반환하고 안정적으로 운영
# 즉, 각 요청마다 새로운 세션을 만들고 요청이 끝나면 세션을 닫아줌
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
