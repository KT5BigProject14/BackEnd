from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


class User(Base):
    __tablename__ = 'users'
    user_id = Column(String(255), primary_key=True, index=True)
    password = Column(String(255))
    user_info = relationship("UserInfo", back_populates="user")
    chats = relationship("Chat", back_populates="user")
    boards = relationship("Board", back_populates="user")
    comments = relationship("Comment", back_populates="user")
    keywords = relationship("Keyword", back_populates="user")


class UserInfo(Base):
    __tablename__ = 'user_info'
    user_id = Column(String(255), ForeignKey(
        'users.user_id'), primary_key=True, index=True)
    name = Column(String(255), index=True)
    email = Column(String(255), unique=True, index=True)
    phone = Column(String(20))
    corporation = Column(String(255))
    business_number = Column(Integer)
    user = relationship("User", back_populates="user_info")


class Country(Base):
    __tablename__ = 'country'
    country_id = Column(String(255), primary_key=True, index=True)
    country = Column(String(255))


class State(Base):
    __tablename__ = 'state'
    state_id = Column(String(255), primary_key=True, index=True)
    country_id = Column(String(255), ForeignKey(
        'country.country_id'), nullable=False)
    state = Column(String(255))
    country = relationship("Country")


class News(Base):
    __tablename__ = 'news'
    news_id = Column(String(255), primary_key=True, index=True)
    state_id = Column(String(255), ForeignKey(
        'state.state_id'), nullable=False)
    country_id = Column(String(255), ForeignKey(
        'country.country_id'), nullable=False)
    title = Column(String(255))
    content = Column(String(255))
    state = relationship("State")
    country = relationship("Country")


class Chat(Base):
    __tablename__ = 'chat'
    chat_id = Column(String(255), primary_key=True, index=True)
    Field6 = Column(String(255))
    user_id = Column(String(255), ForeignKey('users.user_id'), nullable=False)
    content = Column(String(255))
    created_at = Column(String(255))
    user = relationship("User", back_populates="chats")


class FAQ(Base):
    __tablename__ = 'FAQ'
    faq_id = Column(String(255), primary_key=True, index=True)
    content = Column(String(255))


class Board(Base):
    __tablename__ = 'board'
    board_id = Column(String(255), primary_key=True, index=True)
    user_id = Column(String(255), ForeignKey('users.user_id'), nullable=False)
    title = Column(String(255))
    content = Column(String(255))
    created_at = Column(String(255))
    user = relationship("User", back_populates="boards")
    comments = relationship("Comment", back_populates="board")


class Comment(Base):
    __tablename__ = 'comment'
    reply_id = Column(String(255), primary_key=True, index=True)
    board_id = Column(String(255), ForeignKey(
        'board.board_id'), nullable=False)
    user_id = Column(String(255), ForeignKey('users.user_id'), nullable=False)
    content = Column(String(255))
    created_at = Column(String(255))
    board = relationship("Board", back_populates="comments")
    user = relationship("User", back_populates="comments")


class Keyword(Base):
    __tablename__ = 'keyword'
    keyword_id = Column(String(255), primary_key=True, index=True)
    user_id = Column(String(255), ForeignKey('users.user_id'), nullable=False)
    keyword = Column(String(255))
    user = relationship("User", back_populates="keywords")
