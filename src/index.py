import asyncio
import traceback
from typing import Any

import httpx
from telethon import TelegramClient, events
from telethon.errors import UsernameInvalidError, UsernameNotOccupiedError
from telethon.utils import get_peer_id

from .config import load_config
from .format import build_message
from .push import build_pushplus_payload, pushplus_send

ChatRule = tuple[str, list[str], bool]


def _should_push(
    text: str,
    mode: str,
    keywords: list[str],
    case_sensitive: bool,
) -> tuple[bool, str | None]:
    normalized_keywords = []
    for kw in keywords:
        token = kw.strip()
        if token:
            normalized_keywords.append(token if case_sensitive else token.lower())

    if not normalized_keywords:
        return True, None

    normalized_text = text if case_sensitive else text.lower()
    hit = next((kw for kw in normalized_keywords if kw in normalized_text), None)

    if mode == "allow":
        return hit is not None, hit
    return hit is None, hit


async def main() -> None:
    try:
        cfg = load_config()
    except Exception as exc:
        print(f"Config error: {exc}")
        traceback.print_exc()
        raise SystemExit(1) from exc

    client = TelegramClient(cfg.session_name, cfg.api_id, cfg.api_hash)
    start_result = client.start(phone=cfg.phone)
    if asyncio.iscoroutine(start_result):
        await start_result

    entities: list[Any] = []
    chat_title_by_id: dict[int, str] = {}
    chat_rule_by_id: dict[int, ChatRule] = {}
    for chat in cfg.chats:
        try:
            entity = await client.get_entity(chat)
        except (UsernameInvalidError, UsernameNotOccupiedError) as exc:
            print(f"Invalid chat entry: {chat}")
            traceback.print_exc()
            raise SystemExit(1) from exc
        entities.append(entity)
        chat_title = getattr(entity, "title", chat)
        peer_id = get_peer_id(entity)
        chat_title_by_id[peer_id] = chat_title
        rule = cfg.chat_filters[chat]
        chat_rule_by_id[peer_id] = (rule.mode, rule.keywords, rule.case_sensitive)

    print(f"Connected. Chats: {', '.join(chat_title_by_id.values())}")

    timeout = httpx.Timeout(cfg.pushplus_timeout)
    async with httpx.AsyncClient(timeout=timeout) as http_client:
        for entity in entities:
            chat_id = get_peer_id(entity)
            chat_title = chat_title_by_id.get(chat_id, str(chat_id))
            previous_messages_raw = await client.get_messages(entity, limit=1)
            if not previous_messages_raw:
                print(f"No messages found in {chat_title}.")
                continue

            last_message_raw = previous_messages_raw[0]
            last_message = build_message(last_message_raw)
            mode, keywords, case_sensitive = chat_rule_by_id[chat_id]
            should_push, hit = _should_push(
                last_message.message,
                mode,
                keywords,
                case_sensitive,
            )
            if not should_push:
                print(
                    f"[FILTER DROP] chat={chat_title} msg_id={last_message.msg_id} mode={mode} hit={hit}"
                )
                continue

            title, content = build_pushplus_payload(chat_title, last_message)
            await pushplus_send(
                http_client,
                cfg,
                title=title,
                content=content,
            )

        @client.on(events.NewMessage(chats=entities))
        async def handler(event):
            try:
                latest_message_raw = event.message
                latest_message = build_message(latest_message_raw)
                event_chat_id = event.chat_id
                chat_title = chat_title_by_id.get(event_chat_id, str(event_chat_id))
                mode, keywords, case_sensitive = chat_rule_by_id.get(
                    event_chat_id,
                    ("allow", [], False),
                )
                should_push, hit = _should_push(
                    latest_message.message,
                    mode,
                    keywords,
                    case_sensitive,
                )
                if not should_push:
                    print(
                        f"[FILTER DROP] chat={chat_title} msg_id={latest_message.msg_id} mode={mode} hit={hit}"
                    )
                    return

                title, content = build_pushplus_payload(chat_title, latest_message)
                await pushplus_send(
                    http_client,
                    cfg,
                    title=title,
                    content=content,
                )
            except Exception as exc:
                print(f"[PUSH ERROR] {exc}")
                traceback.print_exc()

        print("Listening for new messages. Press Ctrl+C to exit.")
        await client.run_until_disconnected()

 
if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Exited.")
