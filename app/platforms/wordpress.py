import httpx

from app.config import settings
from app.platforms.common import failure, success


async def post(message: str):
    """Publish the message as a WordPress post using an application password."""
    name = "WordPress"
    credentials = (
        settings.wordpress_base_url,
        settings.wordpress_username,
        settings.wordpress_app_password,
    )
    if not all(credentials):
        return failure(name, "Missing WordPress site URL, username, or application password.")

    base_url = settings.wordpress_base_url.rstrip("/")
    if not base_url.lower().startswith("https://"):
        return failure(name, "WordPress site URL must use HTTPS when sending application credentials.")

    try:
        async with httpx.AsyncClient(
            timeout=20,
            auth=(settings.wordpress_username, settings.wordpress_app_password),
        ) as client:
            response = await client.post(
                f"{base_url}/wp-json/wp/v2/posts",
                json={"title": "Update", "content": message, "status": "publish"},
            )
        if response.status_code not in (200, 201):
            return failure(name, f"WordPress API returned HTTP {response.status_code}.")

        post_url = response.json().get("link")
        return success(name, post_url, bool(post_url))
    except (httpx.HTTPError, ValueError, TypeError):
        return failure(name, "WordPress request failed. Check the site and application password.")
