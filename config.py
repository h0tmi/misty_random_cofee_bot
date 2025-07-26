import os
from dataclasses import dataclass


@dataclass
class Config:
    bot_token: str
    database_path: str = "bot.db"
    admin_ids: list = None


def load_config() -> Config:
    return Config(
        bot_token=os.getenv("BOT_TOKEN", "YOUR_BOT_TOKEN_HERE"),
        admin_ids=[561189061]  # Замените на ваш Telegram ID
    )
