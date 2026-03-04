import os
from dotenv import load_dotenv


load_dotenv()


def _read_token_from_file(path: str) -> str:
    if not os.path.exists(path):
        return ""
    with open(path, "r", encoding="utf-8") as f:
        return f.read().strip()


BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()
if not BOT_TOKEN:
    BOT_TOKEN = _read_token_from_file("token_bot.txt")
if not BOT_TOKEN:
    BOT_TOKEN = _read_token_from_file("bot_token.txt")

# URL мини-приложения (FastAPI)
WEBAPP_URL = os.getenv("WEBAPP_URL", "https://example.com")
WEBAPP_HOST = os.getenv("WEBAPP_HOST", "0.0.0.0")
WEBAPP_PORT = int(os.getenv("WEBAPP_PORT", "8000"))
