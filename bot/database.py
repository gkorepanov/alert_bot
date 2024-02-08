"""Database module for the bot.
Uses async Beanie client for MongoDB: https://github.com/roman-right/beanie
"""
# general imports
from typing import Optional, Set
import logging

# telegram imports
from telegram.constants import ChatType, ChatMemberStatus

# mongodb imports
from motor.motor_asyncio import AsyncIOMotorClient
from beanie import Document, init_beanie
from pydantic import Field

# project imports
from .config import config

# logger
logger = logging.getLogger(__name__)

# custom id definitions
UserId = ChatId = MessageId = int
PhotoId = str


class DBUser(Document):
    id: UserId = Field(..., description="Telegram-based user id")
    username: Optional[str] = Field(default=None)
    phone_number: Optional[str] = Field(default=None)


class DBChat(Document):
    id: ChatId = Field(..., description="Telegram-based chat id")
    adder_user_id: Optional[UserId] = Field(default=None, description="User id of the user who added the bot to the chat")
    bot_status: ChatMemberStatus = Field(default=ChatMemberStatus.MEMBER, description="Bot status in the chat")
    name: Optional[str] = Field(default=None, description="Name of the chat")
    chat_type: Optional[ChatType] = Field(default=None, description="Type of the chat")
    alert_users: Set[UserId] = Field(default=[], description="Users to alert")
    alerts: Set[str] = Field(default=[], description="Alert regexps to trigger")
    muted: bool = Field(default=False, description="Muted state of the chat")


async def init_database():
    """Initialize database connection and models.
    Should be globally called before any database operations.
    """
    client = AsyncIOMotorClient(config.mongodb_uri)

    await init_beanie(database=client.bot, document_models=[
        DBUser,
        DBChat,
    ])
