import logging

from telegram import Bot
from bot.database import DBChat, DBUser
from bot.config import config
import httpx


logger = logging.getLogger(__name__)


async def alert_user(bot: Bot, db_user: DBUser, db_chat: DBChat, text: str):
    try:
        text = f"Alert from chat {db_chat.name}: {text}"
        await bot.send_message(
            chat_id=db_user.id,
            text=text,
        )
        if db_user.phone_number is not None:
            await call_phone_number(db_user.phone_number, text)
    except Exception:
        logger.exception("Exception while alerting user")


async def call_phone_number(phone_number: str, text: str):
    client = httpx.AsyncClient(timeout=10)
    response = await client.get(
        url=config.call_api_url,
        params={
            **config.call_api_kwargs,
            "phone": phone_number,
            "text": text,
        },
    )
    if response.json().get("status") == "error":
        raise ValueError(f"Error while calling phone number: {response.json()}")
