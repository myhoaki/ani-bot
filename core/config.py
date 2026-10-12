import os

from dotenv import load_dotenv

load_dotenv()


def get_required_env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"{name} is not set")
    return value


DISCORD_TOKEN = get_required_env("DISCORD_TOKEN")
KAT_BOT_ID = int(get_required_env("KAT_BOT_ID"))

GEMINI_API_KEY = get_required_env("GEMINI_API_KEY")
GEMINI_MODEL = os.getenv(
    "GEMINI_MODEL",
    "gemini-3.5-flash-lite",
)
GEMINI_TEMPERATURE = float(
    os.getenv("GEMINI_TEMPERATURE", "1.1")
)
GEMINI_MAX_OUTPUT_TOKENS = int(
    os.getenv("GEMINI_MAX_OUTPUT_TOKENS", "180")
)

MIN_TURNS = int(os.getenv("MIN_TURNS", "3"))
MAX_TURNS = int(os.getenv("MAX_TURNS", "8"))
RESPONSE_TIMEOUT = int(
    os.getenv("KAT_RESPONSE_TIMEOUT", "90")
)
HISTORY_LIMIT = int(os.getenv("HISTORY_LIMIT", "12"))
