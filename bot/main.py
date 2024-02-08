"""Main entrypoint which runs the bot and the webserver in the same event loop.

We need to run the bot and the webserver in the same event loop,
see https://stackoverflow.com/questions/76142431/how-to-run-another-application-within-the-same-running-event-loop
for options on how to do it.

I chose this code pattern because uvicorn provides a way to run the webserver
in existing event loop, while PTB does whole event loop management itself.
"""
# general imports
import logging

# webserver imports
import uvicorn

# telegram imports
from telegram.error import TelegramError

# project imports
from bot.app import get_ptb_application
from bot.backend import fastapi_app
from bot.database import init_database

# logger
logger = logging.getLogger(__name__)


async def run_bot_and_webserver():
    """The code mostly mimics the code from `telegram.ext.Application.run_polling()`
    from https://github.com/python-telegram-bot/python-telegram-bot/blob/v20.7/telegram/ext/_application.py#L698
    """
    # database initialization
    await init_database()

    # webserver initialization
    config = uvicorn.Config(fastapi_app, host='0.0.0.0', port=8000)
    server = uvicorn.Server(config)

    # telegram bot initialization
    app = get_ptb_application()

    fastapi_app.state.ptb_app = app

    try:
        # telegram bot initialization
        try:
            await app.initialize()
            if app.post_init:
                await app.post_init(app)

            def error_callback(exc: TelegramError) -> None:
                app.create_task(app.process_error(error=exc, update=None))
            await app.updater.start_polling(
                drop_pending_updates=False,
                error_callback=error_callback,
            )
            await app.start()
        except Exception:
            raise

        # blocking webserver serving
        await server.serve()

    finally:
        # telegram bot shutdown
        try:
            if app.updater.running:
                await app.updater.stop()
            if app.running:
                await app.stop()
            if app.post_stop:
                await app.post_stop(app)
            await app.shutdown()
            if app.post_shutdown:
                await app.post_shutdown(app)
        finally:
            pass
