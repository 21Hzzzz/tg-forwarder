import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


@dataclass
class Config:
    api_id: int
    api_hash: str
    phone: str
    session_name: str
    chat: str
    pushplus_token: str
    pushplus_timeout: int

def load_config() -> Config:
    project_root = Path(__file__).resolve().parent.parent
    load_dotenv(project_root / ".env")

    api_id_raw = os.getenv("TG_API_ID", "").strip()
    api_hash = os.getenv("TG_API_HASH", "").strip()
    chat = os.getenv("TG_CHAT", "").strip()
    phone = os.getenv("TG_PHONE", "").strip()
    pushplus_token = os.getenv("PUSHPLUS_TOKEN", "").strip()
    pushplus_timeout_raw = os.getenv("PUSHPLUS_TIMEOUT", "10").strip()
    session_name = os.getenv("TG_SESSION", "tg_forwarder").strip()

    if not api_id_raw:
        raise ValueError("Missing env: TG_API_ID")
    if not api_hash:
        raise ValueError("Missing env: TG_API_HASH")
    if not chat:
        raise ValueError("Missing env: TG_CHAT")
    if not phone:
        raise ValueError("Missing env: TG_PHONE")
    if not pushplus_token:
        raise ValueError("Missing env: PUSHPLUS_TOKEN")

    try:
        api_id = int(api_id_raw)
    except ValueError as exc:
        raise ValueError("Invalid env: TG_API_ID must be an integer") from exc

    try:
        pushplus_timeout = int(pushplus_timeout_raw)
    except ValueError as exc:
        raise ValueError("Invalid env: PUSHPLUS_TIMEOUT must be an integer") from exc

    return Config(
        api_id=api_id,
        api_hash=api_hash,
        phone=phone,
        session_name=session_name,
        chat=chat,
        pushplus_token=pushplus_token,
        pushplus_timeout=pushplus_timeout,
    )
