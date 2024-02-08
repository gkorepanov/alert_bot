# general imports
import logging
import httpx

# telegram imports
from telegram import Bot

# project imports
from .database import DBChat, DBUser
from .config import config


# logger
logger = logging.getLogger(__name__)


async def alert_user(bot: Bot, db_user: DBUser, db_chat: DBChat, text: str) -> None:
    text = f"Alert from chat {db_chat.name}: {text}"
    await bot.send_message(
        chat_id=db_user.id,
        text=text,
    )
    if db_user.phone_number is not None:
        await call_phone_number(db_user.phone_number, text)


async def call_phone_number(phone_number: str, text: str) -> None:
    client = httpx.AsyncClient(timeout=10)
    response = await client.get(
        url=config.call_api_url,
        params={
            **config.call_api_kwargs,
            "phone": phone_number,
            "text": text,
        },
    )
    result = response.json()
    if result.get("status") == "error":
        raise ValueError(f"Error while calling phone number: {result}")
