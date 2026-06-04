from pydantic import BaseModel


class WeChatUserProfile(BaseModel):
    openid: str
    nickname: str | None = None
    avatar_url: str | None = None


class WeChatService:
    """Boundary for WeChat login, subscription messages, and media safety checks."""

    def login_with_code(self, code: str) -> WeChatUserProfile:
        # TODO: Call WeChat auth.code2Session with configured app id/secret.
        return WeChatUserProfile(openid=f"dev_{code[:16]}")

    def schedule_review_reminder(self, user_id: str, concept_id: int) -> dict[str, str | int]:
        # TODO: Send WeChat subscription message after the user grants template permission.
        return {"status": "queued", "user_id": user_id, "concept_id": concept_id}
