import httpx

from config import Config
from format import Message, MessageType

PUSHPLUS_API_URL = "http://www.pushplus.plus/send"


def build_pushplus_payload(message: Message, chat_title: str) -> tuple[str, str]:
    type_label_map = {
        MessageType.NEW_TWEET: "NEW_TWEET",
        MessageType.DELETED_TWEET: "DELETED_TWEET",
        MessageType.NEW_TWEET_REPLY: "NEW_TWEET_REPLY",
        MessageType.UNKNOWN: "UNKNOWN",
    }
    type_label = type_label_map.get(message.message_type, "UNKNOWN")
    title = f"{chat_title} [{type_label}]"

    parts = [
        f"time: {message.time}",
        f"type: {message.message_type.value}",
        f"message:\n{message.message or '<empty>'}",
    ]
    if message.media_url:
        parts.append(f"media_url: {message.media_url}")
    if message.media_description:
        parts.append(f"media_description: {message.media_description}")

    content = "\n\n".join(parts)
    return title, content


async def pushplus_send(
    http_client: httpx.AsyncClient,
    cfg: Config,
    title: str,
    content: str,
) -> None:
    safe_content = (
        content.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace("\n", "<br>")
    )
    payload = {
        "token": cfg.pushplus_token,
        "title": title,
        "content": safe_content,
        "template": "html",
        "channel": "app",
    }
    resp = await http_client.post(PUSHPLUS_API_URL, json=payload)
    resp.raise_for_status()
    data = resp.json()
    if data.get("code") != 200:
        raise RuntimeError(f"PushPlus failed: {data}")
