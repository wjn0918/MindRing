from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.services.wechat import WeChatService, WeChatUserProfile

router = APIRouter(prefix="/api/wechat", tags=["wechat"])


class LoginPayload(BaseModel):
    code: str = Field(min_length=1)


class ReminderPayload(BaseModel):
    user_id: str = Field(min_length=1)
    concept_id: int


@router.post("/login", response_model=WeChatUserProfile)
def login(payload: LoginPayload) -> WeChatUserProfile:
    return WeChatService().login_with_code(payload.code)


@router.post("/review-reminders")
def schedule_review_reminder(payload: ReminderPayload) -> dict[str, str | int]:
    return WeChatService().schedule_review_reminder(payload.user_id, payload.concept_id)
