"""텔레그램 봇 API — 복약·주가 알림 발송."""

from __future__ import annotations

import os

import requests

CALLBACK_MED_TAKEN = "med_taken"


def _api_url(method: str) -> str:
    token = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
    if not token:
        raise ValueError("TELEGRAM_BOT_TOKEN을 .env 또는 GitHub Secret에 설정해 주세요.")
    return f"https://api.telegram.org/bot{token}/{method}"


def _chat_id() -> str:
    chat_id = os.getenv("TELEGRAM_CHAT_ID", "").strip()
    if not chat_id:
        raise ValueError(
            "TELEGRAM_CHAT_ID를 설정해 주세요. "
            "(봇에게 /start 보낸 뒤 scripts/telegram_get_chat_id.py 실행)"
        )
    return chat_id


def _send_message(*, text: str, reply_markup: dict | None = None) -> int:
    payload: dict = {"chat_id": _chat_id(), "text": text}
    if reply_markup:
        payload["reply_markup"] = reply_markup
    response = requests.post(_api_url("sendMessage"), json=payload, timeout=15)
    response.raise_for_status()
    data = response.json()
    if not data.get("ok"):
        raise RuntimeError(f"텔레그램 발송 실패: {data}")
    message_id = data["result"]["message_id"]
    print(f"텔레그램 발송 완료 (message_id={message_id})")
    return message_id


def send_medication_reminder(text: str) -> int:
    """복약 알림 + 「먹었어요 ✅」 버튼. 누르면 Worker Webhook이 복용 완료로 변경."""
    return _send_message(
        text=f"💊 {text}",
        reply_markup={
            "inline_keyboard": [
                [{"text": "먹었어요 ✅", "callback_data": CALLBACK_MED_TAKEN}]
            ]
        },
    )


def send_stock_quotes_alert(body: str, *, link: str | None = None) -> int:
    """미국 주식·지수 시세 — 텔레그램 메시지 + 네이버 증권 링크 버튼."""
    url = link or "https://m.stock.naver.com/worldstock/home"
    return _send_message(
        text=f"📈 <주가보고>\n\n{body}",
        reply_markup={
            "inline_keyboard": [[{"text": "네이버 증권", "url": url}]]
        },
    )
