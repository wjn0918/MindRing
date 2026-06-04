from dataclasses import dataclass

from app.core.config import get_settings


@dataclass(frozen=True)
class SafetyResult:
    allowed: bool
    reason: str = ""


class ContentSafetyService:
    """Content safety abstraction for WeChat msgSecCheck/mediaCheckAsync integration.

    The MVP keeps this as a service boundary so production can plug in WeChat's official
    security.msgSecCheck and security.mediaCheckAsync APIs before mini-program review.
    """

    def check_text(self, content: str) -> SafetyResult:
        settings = get_settings()
        if not settings.enable_content_safety:
            return SafetyResult(allowed=True)

        # TODO: Exchange app credentials for an access token and call WeChat msgSecCheck.
        # Keep the fail-closed behavior when safety is enabled but integration is incomplete.
        return SafetyResult(
            allowed=False, reason="WeChat msgSecCheck integration is not configured"
        )
