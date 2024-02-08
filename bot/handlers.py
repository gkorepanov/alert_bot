import logging
import re

from telegram import Update
from telegram.ext import CallbackContext
from telegram.constants import ParseMode, ChatType, ChatMemberStatus
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ChatMemberHandler,
    filters,
)

from .database import DBChat, DBUser
from .alert import alert_user


logger = logging.getLogger(__name__)


def register_handlers(application: Application, user_filter: filters.BaseFilter):
    application.add_error_handler(error_handler)
    chat_filter = filters.ChatType.GROUPS | filters.ChatType.CHANNEL
    application.add_handler(CommandHandler("start", start_handler, filters=user_filter & filters.ChatType.PRIVATE))
    application.add_handler(CommandHandler("set_phone_number", set_phone_number_handler, filters=user_filter & filters.ChatType.PRIVATE))
    application.add_handler(CommandHandler("alert_me", alert_me_handler, filters=user_filter & chat_filter))
    application.add_handler(CommandHandler("add_alert", add_alert_handler, filters=user_filter & chat_filter))
    application.add_handler(CommandHandler("remove_alerts", remove_alerts_handler, filters=user_filter & chat_filter))
    application.add_handler(CommandHandler("mute", mute_handler, filters=user_filter & chat_filter))
    application.add_handler(CommandHandler("unmute", unmute_handler, filters=user_filter & chat_filter))
    application.add_handler(MessageHandler(filters=chat_filter, callback=message_handler))
    application.add_handler(ChatMemberHandler(added_to_chat_handler))


async def error_handler(update: Update, context: CallbackContext) -> None:
    logger.error(msg=f"Exception while handling an update:", exc_info=context.error)


async def message_handler(update: Update, context: CallbackContext) -> None:
    chat = update.effective_chat
    db_chat: DBChat = await DBChat.get(chat.id)
    if db_chat is None:
        return

    if db_chat.muted:
        return

    for regex in db_chat.alerts:
        if re.search(regex, update.message.text):
            await update.message.reply_text(
                text=f"Alert triggered by regex {regex}",
            )
            for user_id in db_chat.alert_users:
                try:
                    db_user = await DBUser.get(user_id)
                    await alert_user(
                        bot=context.bot,
                        db_user=db_user,
                        db_chat=db_chat,
                        text=update.message.text,
                    )
                except Exception as e:
                    logger.exception(f"Error while alerting user {user_id}: {e}")
            break


async def added_to_chat_handler(update: Update, context: CallbackContext) -> None:
    if update.my_chat_member is None:
        return
    chat = update.my_chat_member.chat
    user = update.my_chat_member.from_user

    if chat.type not in (ChatType.GROUP, ChatType.SUPERGROUP, ChatType.CHANNEL):
        return

    new_status = update.my_chat_member.new_chat_member.status
    db_chat = await DBChat.get(chat.id)
    if db_chat is None:
        db_chat = DBChat(id=chat.id)
    db_chat.name = chat.effective_name
    db_chat.bot_status = new_status
    db_chat.chat_type = chat.type

    if new_status in (
        ChatMemberStatus.LEFT,
        ChatMemberStatus.BANNED,
        ChatMemberStatus.RESTRICTED,
    ):
        db_chat.adder_user_id = None
    elif db_chat.adder_user_id is None:
        db_chat.adder_user_id = user.id

    await db_chat.save()
    await context.bot.send_message(
        chat_id=chat.id,
        text=(
            f"Hello! I am a bot that will alert people when some message is sent to this chat.\n"
            "Use /alert_me to add yourself to alert list for this chat.\n"
            "Use /add_alert <regex> to add alert.\n"
            "Use /remove_alerts to remove all alerts."
        ),
    )


async def start_handler(update: Update, context: CallbackContext) -> None:
    user = update.effective_user
    if (await DBUser.get(user.id)) is None:
        db_user = DBUser(id=user.id, username=user.username)
        await db_user.save()
    await update.effective_message.reply_text(
        text=(
            "Hello!\n"
            "I am a bot that will alert people when some message is sent to chats you add me to.\n"
            "<b>Private chat commands:</b>\n"
            "/set_phone_number +79XXXXXXXXX - to set phone number for calls\n"
            "<b>Group chat commands:</b>\n"
            "/alert_me - to add you to alert list for this chat\n"
            "/add_alert REGEXP - to add alert\n"
            "/remove_alerts - to remove all alerts"
        ),
        parse_mode=ParseMode.HTML,
    )

async def set_phone_number_handler(update: Update, context: CallbackContext) -> None:
    db_user: DBUser = await DBUser.get(update.effective_user.id)

    if not context.args:
        await update.effective_message.reply_text(
            text="You have not provided phone number. Deleted your phone number. I will not call you anymore.",
        )
        db_user.phone_number = None
        await db_user.save()
        return

    phone_number = ''.join(context.args).replace(' ', '')
    if not phone_number.startswith('+79'):
        await update.effective_message.reply_text(
            text="Phone number should start with +79...",
        )
        return

    db_user.phone_number = phone_number
    await db_user.save()
    await update.effective_message.reply_text(
        text=f"Phone number set to {phone_number}.",
    )


async def alert_me_handler(update: Update, context: CallbackContext) -> None:
    chat = update.effective_chat
    db_chat: DBChat = await DBChat.get(chat.id)
    if chat.type == ChatType.CHANNEL:
        user_id = db_chat.adder_user_id
    else:
        user_id = update.effective_user.id

    db_user: DBUser = await DBUser.get(user_id)

    if db_user is None:
        await update.effective_message.reply_text(
            text="You are not registered in the database. Please start a private chat with me first.",
        )
        return
    db_chat.alert_users.add(db_user.id)
    await db_chat.save()
    await update.effective_message.reply_text(
        text="You are added to alert list for this chat.",
    )


async def add_alert_handler(update: Update, context: CallbackContext) -> None:
    chat = update.effective_chat
    db_chat: DBChat = await DBChat.get(chat.id)
    if not context.args:
        await update.message.reply_text(
            text="You have not provided a regex.",
        )
        return

    regex = ' '.join(context.args)
    db_chat.alerts.add(regex)
    await db_chat.save()
    await update.message.reply_text(
        text=f"Alert `{regex}` added.",
        parse_mode=ParseMode.MARKDOWN,
    )


async def remove_alerts_handler(update: Update, context: CallbackContext) -> None:
    chat = update.effective_chat
    db_chat: DBChat = await DBChat.get(chat.id)
    db_chat.alerts.clear()
    await db_chat.save()
    await update.message.reply_text(
        text="Alerts removed.",
    )


async def mute_handler(update: Update, context: CallbackContext) -> None:
    chat = update.effective_chat
    db_chat: DBChat = await DBChat.get(chat.id)
    db_chat.muted = True
    await db_chat.save()
    await update.message.reply_text(
        text="Muted.",
    )

async def unmute_handler(update: Update, context: CallbackContext) -> None:
    chat = update.effective_chat
    db_chat: DBChat = await DBChat.get(chat.id)
    db_chat.muted = False
    await db_chat.save()
    await update.message.reply_text(
        text="Unmuted.",
    )
