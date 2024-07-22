from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from core.config import settings

engine = create_engine(
    settings.SQLALCHEMY_DATABASE_URL,
    pool_size=20,  # 기본 연결 풀 크기
    max_overflow=30,  # 오버플로우 한계
    pool_timeout=30,  # 연결 시도 타임아웃 (초)
    pool_recycle=3600,  # 연결 재활용 시간 (초)
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
