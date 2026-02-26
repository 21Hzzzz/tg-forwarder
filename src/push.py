import asyncio
import html
import httpx

from .config import Config
from .format import Message, is_6551_message, parse_message


PUSHPLUS_API_URL = "https://www.pushplus.plus/send"
PUSHPLUS_MAX_RETRIES = 3
PUSHPLUS_RETRY_BASE_DELAY_SECONDS = 1.0

def _safe_text(s: object) -> str:
    return html.escape(str(s), quote=False).replace("\n", "<br>")

def build_pushplus_payload(chat_title: str, message: Message) -> tuple[str, str]:
    if is_6551_message(message.message):
        parsed = parse_message(message.message)

        title = f"{parsed[0]['username']} [{parsed[0]['event']}]"

        if parsed[0]["event"] == "新推文":
            parts = [
                f"{parsed[0]['data']['tweet']}",
            ]
        elif parsed[0]["event"] == "新推文回复":
            parts = [
                f"上文内容:\n{parsed[0]['data']['parent']}",
                f"回帖内容:\n{parsed[0]['data']['reply']}",
            ]
        elif parsed[0]["event"] == "新关注动态":
            followed_users = "\n".join(parsed[0]["data"]["followed_users"])
            parts = [
                f"关注用户:\n{followed_users}",
            ]
        elif parsed[0]["event"] == "删除推文回复":
            parts = [
                f"上文内容:\n{parsed[0]['data']['parent']}",
                f"回帖内容:\n{parsed[0]['data']['reply']}",
            ]
        elif parsed[0]["event"] == "删除推文":
            parts = [
                f"",
            ]
        elif parsed[0]["event"] == "新推文引用":
            parts = [
                f"引用内容:\n{parsed[0]['data']['quote']}",
            ]
        else:
            parts = [
                f"",
            ]
    else:
        title = chat_title
        parts = [
            f"{message.message}",
        ]

    html_parts = []

    for p in parts:
        html_parts.append(_safe_text(p))

    html_parts.append(_safe_text(message.time))

    if message.media_url:
        html_parts.append(f'media_url:<br><a href="{message.media_url}">{message.media_url}</a>')

    if message.media_description:
        html_parts.append(_safe_text(f"media_description:\n{message.media_description}"))

    content = "<br><br>".join(html_parts)
    return title, content


async def pushplus_send(
    http_client: httpx.AsyncClient,
    cfg: Config,
    title: str,
    content: str,
) -> None:
    payload = {
        "token": cfg.pushplus_token,
        "title": title,
        "content": content,
        "template": "html",
        "channel": "app",
    }
    last_error: Exception | None = None

    for attempt in range(1, PUSHPLUS_MAX_RETRIES + 1):
        try:
            resp = await http_client.post(PUSHPLUS_API_URL, json=payload)
            resp.raise_for_status()
            data = resp.json()
            if data.get("code") != 200:
                raise RuntimeError(f"PushPlus failed: {data}")
            return
        except (httpx.HTTPError, RuntimeError) as exc:
            last_error = exc
            if attempt == PUSHPLUS_MAX_RETRIES:
                break
            backoff = PUSHPLUS_RETRY_BASE_DELAY_SECONDS * (2 ** (attempt - 1))
            await asyncio.sleep(backoff)

    raise RuntimeError(
        f"PushPlus failed after {PUSHPLUS_MAX_RETRIES} attempts: {last_error}"
    ) from last_error
