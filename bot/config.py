# general imports
from typing import Set, Optional, Dict
from pathlib import Path

# pydantic imports
from pydantic_settings import BaseSettings


config_dir = Path(__file__).parent.parent.resolve() / "config"
bot_dir = Path(__file__).parent.parent.resolve() / "bot"


class Settings(BaseSettings):
    """All settings are parsed from environment.
    """
    telegram_token: str
    allowed_telegram_usernames: Set[str] = set()

    mongodb_uri: str = "mongodb://mongo:27017"

    call_api_url: Optional[str] = "https://zvonok.com/manager/cabapi_external/api/v1/phones/call/"
    call_api_kwargs: Optional[Dict[str, str]] = {
        "public_key": "your_public_key",
        "campaign_id": "your_campaign_id",
    }



# global config
config = Settings()
