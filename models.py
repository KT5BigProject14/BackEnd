from sqlalchemy import Column, Integer, String, ForeignKey, Boolean, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from sqlalchemy.orm import Session
from sqlalchemy import event

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    email = Column(String(255), primary_key=True, unique=True, index=True)
    password = Column(String(255))
    user_name = Column(String(255), index=True)
    user_info = relationship("UserInfo", back_populates="user", uselist=False)
    qna = relationship("QnA", back_populates="user")
    comments = relationship("Comment", back_populates="user")

class UserInfo(Base):
    __tablename__ = 'user_info'
    user_info_id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), ForeignKey('users.email'), unique=True, index=True)
    position = Column(String(100))
    phone = Column(String(20))
    corporation = Column(String(255))
    business_number = Column(Integer)
    user = relationship("User", back_populates="user_info")

class QnA(Base):
    __tablename__ = 'qna'
    qna_id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), ForeignKey('users.email'), nullable=False)
    title = Column(String(255))
    content = Column(String(255))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    user = relationship("User", back_populates="qna")
    comments = relationship("Comment", back_populates="qna")
    images = relationship("Image", back_populates="qna")

class Comment(Base):
    __tablename__ = 'comment'
    comment_id = Column(Integer, primary_key=True, index=True)
    qna_id = Column(Integer, ForeignKey('qna.qna_id'), nullable=False)
    email = Column(String(255), ForeignKey('users.email'), nullable=False)
    content = Column(String(255))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    qna = relationship("QnA", back_populates="comments")
    user = relationship("User", back_populates="comments")
    images = relationship("Image", back_populates="comment")

class Image(Base):
    __tablename__ = 'image'
    image_id = Column(Integer, primary_key=True, index=True)
    qna_id = Column(Integer, ForeignKey('qna.qna_id'), nullable=True)
    comment_id = Column(Integer, ForeignKey('comment.comment_id'), nullable=True)
    image_name = Column(String(255))
    qna = relationship("QnA", back_populates="images")
    comment = relationship("Comment", back_populates="images")

class emailAuth(Base):
    __tablename__ = 'email_auth'
    emailAuth_id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    verify_number = Column(String(10), nullable=False)
    is_active = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


@event.listens_for(Session, "before_flush")
def receive_before_flush(session, flush_context, instances):
    for instance in session.dirty:
        if isinstance(instance, User):
            instance.updated_at = func.now()
