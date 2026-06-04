from typing import Annotated
from sqlalchemy import select
from datetime import date

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.auth import create_access_token
from app.db.session import get_db
from app.models import User
from app.schemas import LoginResponse, UserRead
from app.services.wechat import WeChatService, WeChatUserProfile

router = APIRouter(prefix="/api/wechat", tags=["wechat"])
DbDep = Annotated[Session, Depends(get_db)]


class LoginPayload(BaseModel):
    code: str = Field(min_length=1)
    nickname: str | None = Field(default=None, max_length=120)
    avatar_url: str | None = Field(default=None, max_length=500)
    birth_date: date | str | None = None


class ReminderPayload(BaseModel):
    user_id: int
    concept_id: int


@router.post("/login", response_model=LoginResponse)
def login(payload: LoginPayload, db: DbDep) -> LoginResponse:
    profile = WeChatService().login_with_code(payload.code)
    
    # 根据 openid 查询用户
    user = db.scalar(select(User).where(User.openid == profile.openid))
    
    nickname = (payload.nickname or profile.nickname or "").strip() or None
    avatar_url = payload.avatar_url or profile.avatar_url
    
    if user is None:
        # 新用户
        user = User(
            openid=profile.openid, 
            nickname=nickname, 
            avatar_url=avatar_url,
            birth_date=payload.birth_date
        )
        db.add(user)
    else:
        # 更新微信头像等登录资料，但不要用微信登录资料覆盖用户手动修改过的昵称
        if not (user.nickname or "").strip() and nickname:
            user.nickname = nickname
        user.avatar_url = avatar_url or user.avatar_url
        if payload.birth_date is not None:
            user.birth_date = payload.birth_date
    
    db.commit()
    db.refresh(user)
    
    # 生成 JWT token
    access_token = create_access_token(data={"user_id": user.id})
    
    return LoginResponse(
        access_token=access_token,
        user=UserRead.model_validate(user)
    )


@router.post("/review-reminders")
def schedule_review_reminder(payload: ReminderPayload) -> dict[str, str | int]:
    return WeChatService().schedule_review_reminder(payload.user_id, payload.concept_id)
