from os import getenv
from pathlib import Path
from typing import Dict

import pytz
from dotenv import load_dotenv
from fastapi import WebSocket

load_dotenv()

BASE_DIR = Path(__file__).parent.resolve()

ENGINE = getenv("ENGINE", "sqlite+aiosqlite:///./infra/database/database.db")

TELEGRAM_BOT_TOKEN = getenv("TELEGRAM_BOT_TOKEN")
HOST = getenv("HOST")
WEBHOOK_URL = getenv("WEBHOOK_HOST", "") + "/webhook"

DEV_MODE = int(getenv("DEV_MODE", 0) or 0)
TEST_MODE = int(getenv("TEST_MODE", 0) or 0)
RESET = int(getenv("RESET", 0) or 0)

TIMEZONE = pytz.timezone(getenv("TIMEZONE", "Europe/Moscow"))

MINIO_ROOT_USER = getenv("MINIO_ROOT_USER")
MINIO_ROOT_PASSWORD = getenv("MINIO_ROOT_PASSWORD")
MINIO_URL = getenv("MINIO_URL")

active_connections = {}
