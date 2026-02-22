from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Optional


class MessageType(str, Enum):
    NEW_TWEET = "new_tweet"
    DELETED_TWEET = "deleted_tweet"
    NEW_TWEET_REPLY = "new_tweet_reply"
    UNKNOWN = "unknown"


@dataclass
class Message:
    msg_id: int
    time: str
    message: str
    media_url: Optional[str] = None
    media_description: Optional[str] = None
    message_type: MessageType = MessageType.UNKNOWN


def format_time(dt: Optional[datetime]) -> str:
    if not isinstance(dt, datetime):
        return "unknown"
    utc8 = timezone(timedelta(hours=8))
    return dt.astimezone(utc8).strftime("%Y-%m-%d %H:%M:%S")


def extract_media_url(msg) -> Optional[str]:
    media = getattr(msg, "media", None)
    webpage = getattr(media, "webpage", None) if media else None
    return getattr(webpage, "url", None) if webpage else None


def extract_media_description(msg) -> Optional[str]:
    media = getattr(msg, "media", None)
    webpage = getattr(media, "webpage", None) if media else None
    return getattr(webpage, "description", None) if webpage else None


def detect_message_type(text: str) -> MessageType:
    first_line = ((text or "").splitlines() or [""])[0].strip()

    if "🌟监控到新推文回复" in first_line or "监控到新推文回复" in first_line:
        return MessageType.NEW_TWEET_REPLY
    if "🌟监控到删除推文" in first_line or "监控到删除推文" in first_line:
        return MessageType.DELETED_TWEET
    if "🌟监控到新推文" in first_line or "监控到新推文" in first_line:
        return MessageType.NEW_TWEET
    return MessageType.UNKNOWN


def build_message(msg) -> Message:
    raw_message = msg.raw_text or msg.message or ""
    media_url = extract_media_url(msg)
    media_description = extract_media_description(msg)
    message_type = detect_message_type(raw_message)

    return Message(
        msg_id=msg.id,
        time=format_time(msg.date),
        message=raw_message,
        media_url=media_url,
        media_description=media_description,
        message_type=message_type,
    )
