import httpx

from fastapi import HTTPException
from pydantic import BaseModel

from app.core.config import get_settings


class WeChatUserProfile(BaseModel):
    openid: str
    nickname: str | None = None
    avatar_url: str | None = None


class WeChatService:
    """Boundary for WeChat login, subscription messages, and media safety checks."""

    def login_with_code(self, code: str) -> WeChatUserProfile:
        settings = get_settings()
        if not settings.wechat_app_id or not settings.wechat_app_secret:
            raise HTTPException(
                status_code=500, detail="请先配置微信 AppID/Secret"
            )

        url = "https://api.weixin.qq.com/sns/jscode2session"
        params = {
            "appid": settings.wechat_app_id,
            "secret": settings.wechat_app_secret,
            "js_code": code,
            "grant_type": "authorization_code",
        }

        try:
            response = httpx.get(url, params=params, timeout=10)
            response.raise_for_status()
        except httpx.HTTPError as e:
            raise HTTPException(
                status_code=500, detail=f"调用微信 API 失败: {str(e)}"
            ) from e

        data = response.json()

        openid = data.get("openid")
        if not openid:
            raise HTTPException(
                status_code=400, detail=f"微信登录失败: {data}"
            )

        return WeChatUserProfile(openid=openid)

    def schedule_review_reminder(self, user_id: int, concept_id: int) -> dict[str, str | int]:
        # TODO: Send WeChat subscription message after the user grants template permission.
        return {"status": "queued", "user_id": user_id, "concept_id": concept_id}
