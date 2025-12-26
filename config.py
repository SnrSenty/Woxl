import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()


@dataclass
class Config:
    BOT_TOKEN: str = os.getenv("BOT_TOKEN", "")
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///woxl.db")
    # HTML parse mode globally
    PARSE_MODE: str = "HTML"


cfg = Config()

if not cfg.BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN is not set. Please set BOT_TOKEN env var.")