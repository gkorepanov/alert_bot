# general imports
import logging

# telegram imports
from telegram.ext import (
    Application,
    ApplicationBuilder,
    filters,
    AIORateLimiter,
)

# project imports
from .config import config
from .handlers import register_handlers
from .database import init_database

# logger
logger = logging.getLogger(__name__)


async def post_init(application: Application):
    await init_database()


def get_ptb_application() -> Application:
    application = (
        ApplicationBuilder()
        .token(config.telegram_token)
        .concurrent_updates(True)
        .rate_limiter(AIORateLimiter(max_retries=3))
        .http_version("1.1")
        .get_updates_http_version("1.1")
        .read_timeout(60)
        .write_timeout(60)
        .connect_timeout(60)
        .pool_timeout(60)
        .connection_pool_size(1024)
        .post_init(post_init)
        .build()
    )

    # filters
    if len(config.allowed_telegram_usernames) == 0:
        user_filter = filters.ALL
    else:
        user_filter = filters.User(username=config.allowed_telegram_usernames)

    register_handlers(application, user_filter)
    return application
