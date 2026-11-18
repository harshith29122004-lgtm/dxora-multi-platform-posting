import httpx

from app.config import settings
from app.platforms.common import failure, success


async def post(message: str):
    """Publish a public member or organisation post through LinkedIn's Posts API."""
    name = "LinkedIn"
    if not settings.linkedin_access_token or not settings.linkedin_author_urn:
        return failure(name, "Missing LINKEDIN_ACCESS_TOKEN or LINKEDIN_AUTHOR_URN.")

    payload = {
        "author": settings.linkedin_author_urn,
        "commentary": message,
        "visibility": "PUBLIC",
        "distribution": {
            "feedDistribution": "MAIN_FEED",
            "targetEntities": [],
            "thirdPartyDistributionChannels": [],
        },
        "lifecycleState": "PUBLISHED",
        "isReshareDisabledByAuthor": False,
    }
    headers = {
        "Authorization": f"Bearer {settings.linkedin_access_token}",
        "LinkedIn-Version": settings.linkedin_api_version,
        "X-Restli-Protocol-Version": "2.0.0",
    }

    try:
        async with httpx.AsyncClient(timeout=20) as client:
            response = await client.post(
                "https://api.linkedin.com/rest/posts",
                json=payload,
                headers=headers,
            )
        if response.status_code not in (200, 201):
            return failure(name, f"LinkedIn API returned HTTP {response.status_code}.")

        post_id = response.headers.get("x-restli-id")
        post_url = f"https://www.linkedin.com/feed/update/{post_id}" if post_id else None
        return success(name, post_url, bool(post_url))
    except httpx.HTTPError:
        return failure(name, "LinkedIn could not be reached. Check the network and try again.")
