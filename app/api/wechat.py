from typing import Annotated

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models import User
from app.services.wechat import WeChatService, WeChatUserProfile

router = APIRouter(prefix="/api/wechat", tags=["wechat"])
DbDep = Annotated[Session, Depends(get_db)]


class LoginPayload(BaseModel):
    code: str = Field(min_length=1)
    nickname: str | None = Field(default=None, max_length=120)
    avatar_url: str | None = Field(default=None, max_length=500)


class ReminderPayload(BaseModel):
    user_id: str = Field(min_length=1)
    concept_id: int


@router.post("/login", response_model=WeChatUserProfile)
def login(payload: LoginPayload, db: DbDep) -> WeChatUserProfile:
    profile = WeChatService().login_with_code(payload.code)
    user = db.get(User, profile.openid)
    nickname = payload.nickname or profile.nickname
    avatar_url = payload.avatar_url or profile.avatar_url
    if user is None:
        user = User(id=profile.openid, nickname=nickname, avatar_url=avatar_url)
        db.add(user)
    else:
        user.nickname = nickname or user.nickname
        user.avatar_url = avatar_url or user.avatar_url
    db.commit()
    return WeChatUserProfile(openid=user.id, nickname=user.nickname, avatar_url=user.avatar_url)


@router.post("/review-reminders")
def schedule_review_reminder(payload: ReminderPayload) -> dict[str, str | int]:
    return WeChatService().schedule_review_reminder(payload.user_id, payload.concept_id)
