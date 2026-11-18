import asyncio
from app.platforms import linkedin, mastodon, bluesky, wordpress, telegram
from app.platforms.common import failure

PLATFORM_POSTERS = [linkedin.post, mastodon.post, bluesky.post, wordpress.post, telegram.post]


async def _post_safely(poster, message: str):
    """Keep a broken provider connector from cancelling the other four posts."""
    try:
        return await poster(message)
    except Exception as exc:
        # Connector exceptions are reduced to their type; secrets and response
        # bodies should never be copied into the API response.
        return failure(poster.__module__.rsplit(".", 1)[-1].replace("_", " ").title(),
                       f"Unexpected connector error ({type(exc).__name__}).")


async def publish_everywhere(message: str):
    return await asyncio.gather(*(_post_safely(poster, message) for poster in PLATFORM_POSTERS))
