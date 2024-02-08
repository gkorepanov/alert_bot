import logging

from bot.app import get_ptb_application



if __name__ == "__main__":
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("fontTools").setLevel(logging.WARNING)

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)-12s :%(name)-15s: %(levelname)-8s %(message)s'
    )
    ptb_app = get_ptb_application()
    ptb_app.run_polling()
