from sqlalchemy.orm import Session
from models import Community, CommunityImage, CommunityComment
from schemas import Community as community_shcema, CheckCommunity, CommunityComment as community_comment_schema, CheckCommunityComment
from passlib.context import CryptContext
from fastapi import FastAPI, Depends, HTTPException
from typing import Annotated
from pydantic import EmailStr

# community 생성
def create_community(db: Session, community: community_shcema):
    community_db = Community(email=community.email,
                             title=community.title, content=community.content)
    db.add(community_db)
    db.commit()
    db.refresh(community_db)
    return community_db

# 커뮤니티 이미지 생성
def create_community_image(db: Session, image: str, community: CheckCommunity):
    community_image = CommunityImage(
        image_name=image, community_id=community.community_id)
    db.add(community_image)
    db.commit()
    db.refresh(community_image)
    return community_image

def read_all_community(db: Session):
    # 모든 커뮤니티 게시글 조회
    all_community = db.query(Community).all()
    
    # 각 커뮤니티 객체에 corporation 및 is_my_post 정보를 추가
    for community in  all_community:
        user = community.user
        community.corporation = user.user_info.corporation if user and user.user_info else None
    
    # 모든 커뮤니티 게시글 반환
    return all_community

# 유저가 선택한 커뮤니티 가져오기
def get_community(db: Session, community_id: int, email: EmailStr):
    community = db.query(Community).filter(Community.community_id == community_id).first()
    user = community.user
    community.corporation = user.user_info.corporation if user and user.user_info else None
    community.is_my_post = True if community.email == email else False
    community_image = db.query(CommunityImage.image_name).filter(
        CommunityImage.community_id == community_id).all()
    community_image = [name[0] for name in community_image]
    return {"community": community, "community_images": community_image}

# 커뮤니티 업데이트
def db_update_community(community: CheckCommunity, db: Session):
    db_community = db.query(Community).filter(
        Community.community_id == community.community_id).first()
    if not db_community:
        raise HTTPException(status_code=404, detail="QnA not found")
    db_community.content = community.content
    db_community.title = community.title
    db.commit()
    db.refresh(db_community)
    return db_community

# 커뮤니티 이미지 삭제
def delete_community_img(community: CheckCommunity, db: Session):
    images_to_delete = db.query(CommunityImage).filter(
        CommunityImage.community_id == community.community_id).all()
    if not images_to_delete:
        return None
    else:
        for db_img in images_to_delete:
            db.delete(db_img)
            db.commit()
        return images_to_delete

# 커뮤니티 삭제
def db_delete_community(community: CheckCommunity, db: Session):
    community_to_delete = db.query(Community).filter(
        Community.community_id == community.community_id).first()
    db.delete(community_to_delete)
    db.commit()

# 커뮤니티 댓글 생성
def create_community_comment(community_comment: CommunityComment, email: EmailStr, db: Session):
    new_comment = CommunityComment(
        community_id=community_comment.community_id, email=email, content=community_comment.content)
    db.add(new_comment)
    db.commit()
    db.refresh(new_comment)
    return new_comment

# 커뮤니티 댓글 가져오기
def get_community_comment(community_id: int, db: Session, email: EmailStr):
    all_community_comment = db.query(CommunityComment).filter(CommunityComment.community_id == community_id).all()
    for comment in all_community_comment:
        comment.corporation = comment.user.user_info.corporation if comment.user and comment.user.user_info else None
        comment.is_my_post = True if comment.email == email else False
    return all_community_comment

# 커뮤니티 댓글 수정
def update_community_comment(comment: CheckCommunityComment, db: Session):
    target_comment = db.query(CommunityComment).filter(
        CommunityComment.community_comment_id == comment.community_comment_id).first()
    target_comment.content = comment.content
    db.commit()
    db.refresh(target_comment)
    return target_comment

# 커뮤니티 댓글 삭제
def delete_community_comment(comment: CheckCommunityComment, db: Session):
    comment_to_delete = db.query(CommunityComment).filter(
        CommunityComment.community_comment_id == comment.community_comment_id).first()
    db.delete(comment_to_delete)
    db.commit()
