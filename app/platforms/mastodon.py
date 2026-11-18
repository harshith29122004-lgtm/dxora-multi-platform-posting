import httpx

from app.config import settings
from app.platforms.common import failure, success


async def post(message: str):
    """Publish a public status on the configured Mastodon instance."""
    name = "Mastodon"
    if not settings.mastodon_access_token:
        return failure(name, "Missing MASTODON_ACCESS_TOKEN.")

    base_url = settings.mastodon_base_url.rstrip("/")
    if not base_url.lower().startswith("https://"):
        return failure(name, "Mastodon instance URL must use HTTPS.")

    try:
        async with httpx.AsyncClient(timeout=20) as client:
            response = await client.post(
                f"{base_url}/api/v1/statuses",
                data={"status": message, "visibility": "public"},
                headers={"Authorization": f"Bearer {settings.mastodon_access_token}"},
            )
        if response.status_code not in (200, 201):
            return failure(name, f"Mastodon API returned HTTP {response.status_code}.")

        post_url = response.json().get("url")
        return success(name, post_url, bool(post_url))
    except (httpx.HTTPError, ValueError, TypeError):
        return failure(name, "Mastodon request failed. Check the instance and token.")
