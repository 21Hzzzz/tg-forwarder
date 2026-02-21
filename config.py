import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


@dataclass
class Config:
    api_id: int
    api_hash: str
    phone: str
    session_name: str
    chat: str
    pushplus_token: str
    pushplus_timeout: int


def load_dotenv(path: str = ".env") -> None:
    env_path = Path(path)
    if not env_path.exists():
        return

    for raw in env_path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip("'").strip('"')
        if key:
            os.environ.setdefault(key, value)


def load_config() -> Config:
    load_dotenv()

    api_id = int(os.getenv("TG_API_ID", "").strip())
    api_hash = os.getenv("TG_API_HASH", "").strip()
    chat = os.getenv("TG_CHAT", "").strip()
    phone = os.getenv("TG_PHONE", "").strip()
    pushplus_token = os.getenv("PUSHPLUS_TOKEN", "").strip()
    pushplus_timeout = int(os.getenv("PUSHPLUS_TIMEOUT", "10").strip())
    session_name = os.getenv("TG_SESSION", "tg_forwarder").strip()

    if not api_id:
        raise ValueError("Missing env: TG_API_ID")
    if not api_hash:
        raise ValueError("Missing env: TG_API_HASH")
    if not chat:
        raise ValueError("Missing env: TG_CHAT")
    if not phone:
        raise ValueError("Missing env: TG_PHONE")
    if not pushplus_token:
        raise ValueError("Missing env: PUSHPLUS_TOKEN")

    return Config(
        api_id=api_id,
        api_hash=api_hash,
        phone=phone,
        session_name=session_name,
        chat=chat,
        pushplus_token=pushplus_token,
        pushplus_timeout=pushplus_timeout,
    )
