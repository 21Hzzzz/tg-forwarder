import asyncio
import traceback

import httpx
from telethon import TelegramClient, events
from telethon.errors import UsernameInvalidError, UsernameNotOccupiedError

from .config import load_config
from .format import build_message
from .push import build_pushplus_payload, pushplus_send

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

    try:
        entity = await client.get_entity(cfg.chat)
    except (UsernameInvalidError, UsernameNotOccupiedError) as exc:
        print(f"Invalid TG_CHAT/TG_CHANNEL: {cfg.chat}")
        traceback.print_exc()
        raise SystemExit(1) from exc

    chat_title = getattr(entity, "title", cfg.chat)
    print(f"Connected. Chat: {chat_title}")

    timeout = httpx.Timeout(cfg.pushplus_timeout)
    async with httpx.AsyncClient(timeout=timeout) as http_client:
        previous_messages_raw = await client.get_messages(entity, limit=1)
        if not previous_messages_raw:
            print("No messages found.")
        else:
            last_message_raw = previous_messages_raw[0]
            last_message = build_message(last_message_raw)
            print(last_message)
            title, content = build_pushplus_payload(last_message, chat_title)
            await pushplus_send(
                http_client,
                cfg,
                title=title,
                content=content,
            )

        @client.on(events.NewMessage(chats=entity))
        async def handler(event):
            try:
                latest_message_raw = event.message
                latest_message = build_message(latest_message_raw)
                title, content = build_pushplus_payload(latest_message, chat_title)
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
