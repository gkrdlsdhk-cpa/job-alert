#!/usr/bin/env python3
"""봇에게 /start 보낸 뒤 chat_id 확인."""

from __future__ import annotations

import os
import sys

import requests
from dotenv import load_dotenv


def main() -> int:
    load_dotenv()
    token = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
    if not token:
        print("TELEGRAM_BOT_TOKEN을 .env에 설정하세요.", file=sys.stderr)
        return 1

    print("텔레그램에서 봇에게 /start 를 보낸 뒤 Enter...")
    input()

    response = requests.get(
        f"https://api.telegram.org/bot{token}/getUpdates",
        timeout=15,
    )
    response.raise_for_status()
    updates = response.json().get("result", [])
    if not updates:
        print("메시지가 없습니다. 봇에게 /start 를 보내고 다시 실행하세요.", file=sys.stderr)
        return 1

    chat_ids: list[int] = []
    for update in updates:
        msg = update.get("message") or update.get("callback_query", {}).get("message")
        if msg and "chat" in msg:
            chat_ids.append(msg["chat"]["id"])

    if not chat_ids:
        print("chat_id를 찾지 못했습니다.", file=sys.stderr)
        return 1

    chat_id = chat_ids[-1]
    print(f"\nTELEGRAM_CHAT_ID={chat_id}")
    print("\n위 값을 .env 와 GitHub Secret에 넣으세요.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
