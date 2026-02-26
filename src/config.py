import os
import json
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


@dataclass
class ChatFilter:
    mode: str
    keywords: list[str]
    case_sensitive: bool = False


@dataclass
class Config:
    api_id: int
    api_hash: str
    phone: str
    session_name: str
    chats: list[str]
    chat_filters: dict[str, ChatFilter]
    pushplus_token: str
    pushplus_timeout: int


def _load_chat_filters_from_json(config_path: Path) -> dict[str, ChatFilter]:
    if not config_path.exists():
        raise ValueError(f"Filter config not found: {config_path}")

    data = json.loads(config_path.read_text(encoding="utf-8"))
    chat_filter_entries = data.get("chat_filters", [])
    if not isinstance(chat_filter_entries, list):
        raise ValueError("Invalid filter config: 'chat_filters' must be a list")

    chat_filters: dict[str, ChatFilter] = {}
    for idx, entry in enumerate(chat_filter_entries, start=1):
        if not isinstance(entry, dict):
            raise ValueError(f"Invalid filter config: chat_filters[{idx}] must be an object")

        chat = str(entry.get("chat", "")).strip()
        if not chat:
            raise ValueError(f"Invalid filter config: chat_filters[{idx}].chat is required")

        mode = str(entry.get("mode", "")).strip().lower()
        if mode not in {"allow", "deny"}:
            raise ValueError(
                f"Invalid filter config: chat_filters[{idx}].mode must be 'allow' or 'deny'"
            )

        keywords_raw = entry.get("keywords", [])
        if not isinstance(keywords_raw, list):
            raise ValueError(f"Invalid filter config: chat_filters[{idx}].keywords must be a list")
        keywords = [str(item) for item in keywords_raw]
        case_sensitive = bool(entry.get("case_sensitive", False))

        chat_filters[chat] = ChatFilter(
            mode=mode,
            keywords=keywords,
            case_sensitive=case_sensitive,
        )

    if not chat_filters:
        raise ValueError("Invalid filter config: 'chat_filters' cannot be empty")

    return chat_filters


def load_config() -> Config:
    project_root = Path(__file__).resolve().parent.parent
    load_dotenv(project_root / ".env")

    api_id_raw = os.getenv("TG_API_ID", "").strip()
    api_hash = os.getenv("TG_API_HASH", "").strip()
    filter_config_path_raw = os.getenv("FILTER_CONFIG_PATH", "").strip()
    phone = os.getenv("TG_PHONE", "").strip()
    pushplus_token = os.getenv("PUSHPLUS_TOKEN", "").strip()
    pushplus_timeout_raw = os.getenv("PUSHPLUS_TIMEOUT", "10").strip()
    session_name = os.getenv("TG_SESSION", "tg_forwarder").strip()

    if not api_id_raw:
        raise ValueError("Missing env: TG_API_ID")
    if not api_hash:
        raise ValueError("Missing env: TG_API_HASH")

    if not filter_config_path_raw:
        raise ValueError("Missing env: FILTER_CONFIG_PATH")
    filter_path = Path(filter_config_path_raw)
    if not filter_path.is_absolute():
        filter_path = project_root / filter_path
    chat_filters = _load_chat_filters_from_json(filter_path)
    chats = list(chat_filters.keys())

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
        chats=chats,
        chat_filters=chat_filters,
        pushplus_token=pushplus_token,
        pushplus_timeout=pushplus_timeout,
    )
