from sqlalchemy import create_engine, Column, Integer, String, ForeignKey, Boolean, DateTime, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker, Session
from sqlalchemy.sql import func
from sqlalchemy import event
from core.config import settings

DATABASE_URL = settings.SQLALCHEMY_DATABASE_URL

engine = create_engine(
    DATABASE_URL,
    pool_size=10,  # 기본 연결 풀 크기
    max_overflow=20,  # 오버플로우 한계
    pool_timeout=60,  # 연결 시도 타임아웃 (초)
    pool_recycle=3600,  # 연결 재활용 시간 (초)
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    email = Column(String(255), primary_key=True, unique=True, index=True)
    password = Column(String(255))
    role = Column(String(50), default="guest")
    user_info = relationship("UserInfo", back_populates="user", uselist=False, cascade="all, delete-orphan")
    qna = relationship("QnA", back_populates="user", cascade="all, delete-orphan")
    comments = relationship("Comment", back_populates="user", cascade="all, delete-orphan")
    docs = relationship("Docs", back_populates="user", cascade="all, delete-orphan")
    keywords = relationship("Keyword", back_populates="user", cascade="all, delete-orphan")
    community = relationship("Community", back_populates="user", cascade="all, delete-orphan")
    community_comments = relationship("CommunityComment", back_populates="user", cascade="all, delete-orphan") 

class UserInfo(Base):
    __tablename__ = 'user_info'
    user_info_id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), ForeignKey('users.email'), unique=True, index=True)
    position = Column(String(100))
    phone = Column(String(20))
    corporation = Column(String(255))
    business_number = Column(String(255))
    user_name = Column(String(255), index=True)
    user = relationship("User", back_populates="user_info")

class QnA(Base):
    __tablename__ = 'qna'
    qna_id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), ForeignKey('users.email'), nullable=False)
    title = Column(String(255))
    content = Column(String(255))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    user = relationship("User", back_populates="qna")
    comments = relationship("Comment", back_populates="qna", cascade="all, delete-orphan")
    images = relationship("Image", back_populates="qna", cascade="all, delete-orphan")

class Comment(Base):
    __tablename__ = 'comment'
    comment_id = Column(Integer, primary_key=True, index=True)
    qna_id = Column(Integer, ForeignKey('qna.qna_id'), nullable=False)
    email = Column(String(255), ForeignKey('users.email'), nullable=False)
    content = Column(String(255))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    qna = relationship("QnA", back_populates="comments")
    user = relationship("User", back_populates="comments")
    images = relationship("Image", back_populates="comment", cascade="all, delete-orphan")

class Image(Base):
    __tablename__ = 'image'
    image_id = Column(Integer, primary_key=True, index=True)
    qna_id = Column(Integer, ForeignKey('qna.qna_id'), nullable=True)
    comment_id = Column(Integer, ForeignKey('comment.comment_id'), nullable=True)
    image_name = Column(String(255))
    qna = relationship("QnA", back_populates="images")
    comment = relationship("Comment", back_populates="images")

class EmailAuth(Base):
    __tablename__ = 'email_auth'
    emailAuth_id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    verify_number = Column(String(10), nullable=False)
    is_active = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

class Docs(Base):
    __tablename__ = 'docs'
    docs_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    email = Column(String(255), ForeignKey('users.email'), nullable=False)
    title = Column(Text)
    content = Column(Text)
    is_like = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    user = relationship("User", back_populates="docs", single_parent=True)  # Add single_parent=True

class Keyword(Base):
    __tablename__ = 'keyword'
    keyword_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    email = Column(String(255), ForeignKey('users.email'), nullable=False)
    likeyear = Column(String(255))
    likecountry = Column(String(255))
    likebusiness = Column(String(255))
    user = relationship("User", back_populates="keywords")

# 이벤트를 통해 User 엔티티의 업데이트 시간을 관리
@event.listens_for(Session, "before_flush")
def receive_before_flush(session, flush_context, instances):
    for instance in session.dirty:
        if isinstance(instance, User):
            instance.updated_at = func.now()

class Community(Base):
    __tablename__ = 'community'
    community_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    email = Column(String(255), ForeignKey('users.email'), nullable=False)
    title = Column(String(255))
    content = Column(String(255))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    user = relationship("User", back_populates="community")
    comments = relationship("CommunityComment", back_populates="community", cascade="all, delete-orphan")
    images = relationship("CommunityImage", back_populates="community", cascade="all, delete-orphan")

class CommunityComment(Base):
    __tablename__ = 'community_comment'
    community_comment_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    community_id = Column(Integer, ForeignKey('community.community_id'), nullable=False)
    email = Column(String(255), ForeignKey('users.email'), nullable=False)
    content = Column(String(255))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    community = relationship("Community", back_populates="comments")
    user = relationship("User", back_populates="community_comments")  # 수정된 부분
    images = relationship("CommunityImage", back_populates="comment", cascade="all, delete-orphan")

class CommunityImage(Base):
    __tablename__ = 'community_image'
    image_id = Column(Integer, primary_key=True, index=True ,autoincrement=True)
    community_id = Column(Integer, ForeignKey('community.community_id'), nullable=True)
    community_comment_id = Column(Integer, ForeignKey('community_comment.community_comment_id'), nullable=True)
    image_name = Column(String(255))
    community = relationship("Community", back_populates="images")
    comment = relationship("CommunityComment", back_populates="images")

Base.metadata.create_all(bind=engine)
