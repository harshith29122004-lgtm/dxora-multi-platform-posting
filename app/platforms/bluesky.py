from datetime import datetime, timezone

import httpx

from app.config import settings
from app.platforms.common import failure, success


async def post(message: str):
    """Create a public Bluesky post using an app password."""
    name = "Bluesky"
    if not settings.bluesky_handle or not settings.bluesky_app_password:
        return failure(name, "Missing BLUESKY_HANDLE or BLUESKY_APP_PASSWORD.")

    try:
        async with httpx.AsyncClient(timeout=25) as client:
            auth_response = await client.post(
                "https://bsky.social/xrpc/com.atproto.server.createSession",
                json={
                    "identifier": settings.bluesky_handle,
                    "password": settings.bluesky_app_password,
                },
            )
            if auth_response.status_code != 200:
                return failure(name, f"Bluesky authentication failed (HTTP {auth_response.status_code}).")

            session = auth_response.json()
            did = session["did"]
            access_token = session["accessJwt"]
            created_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
            record = {
                "$type": "app.bsky.feed.post",
                "text": message,
                "createdAt": created_at,
            }
            post_response = await client.post(
                "https://bsky.social/xrpc/com.atproto.repo.createRecord",
                headers={"Authorization": f"Bearer {access_token}"},
                json={
                    "repo": did,
                    "collection": "app.bsky.feed.post",
                    "record": record,
                },
            )
            if post_response.status_code != 200:
                return failure(name, f"Bluesky post failed (HTTP {post_response.status_code}).")

            uri = post_response.json().get("uri", "")
            record_key = uri.rsplit("/", 1)[-1]
            if not record_key:
                return failure(name, "Bluesky accepted the request but did not return a post record key.")

            profile = settings.bluesky_handle.lstrip("@")
            return success(name, f"https://bsky.app/profile/{profile}/post/{record_key}", True)
    except (httpx.HTTPError, KeyError, ValueError, TypeError):
        return failure(name, "Bluesky request failed. Check the credentials and try again.")
