from datetime import datetime, timezone
from app.schemas import PlatformResult


def success(platform: str, url: str | None, public: bool = False) -> PlatformResult:
    posted_at = datetime.now(timezone.utc)
    return PlatformResult(
        platform=platform,
        status="success",
        posted_url=url,
        public_access=public,
        date=posted_at.date().isoformat(),
        time=posted_at.time().replace(microsecond=0).isoformat() + "Z",
    )


def failure(platform: str, message: str) -> PlatformResult:
    return PlatformResult(platform=platform, status="failed", error=message[:300])
