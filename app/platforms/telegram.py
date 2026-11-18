import httpx

from app.config import settings
from app.platforms.common import failure, success


async def post(message: str):
    """Send the message to a Telegram chat or channel using a bot."""
    name = "Telegram"
    if not settings.telegram_bot_token or not settings.telegram_chat_id:
        return failure(name, "Missing TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID.")

    endpoint = f"https://api.telegram.org/bot{settings.telegram_bot_token}/sendMessage"
    try:
        async with httpx.AsyncClient(timeout=20) as client:
            response = await client.post(
                endpoint,
                json={
                    "chat_id": settings.telegram_chat_id,
                    "text": message,
                    "link_preview_options": {"is_disabled": False},
                },
            )
        if response.status_code != 200:
            return failure(name, f"Telegram API returned HTTP {response.status_code}.")

        payload = response.json()
        if not payload.get("ok"):
            return failure(name, "Telegram did not accept the message.")

        result = payload.get("result", {})
        chat = result.get("chat", {})
        username = chat.get("username")
        message_id = result.get("message_id")
        post_url = f"https://t.me/{username}/{message_id}" if username and message_id else None
        return success(name, post_url, bool(post_url))
    except (httpx.HTTPError, ValueError, TypeError):
        return failure(name, "Telegram request failed. Check the bot and destination chat.")
