"""텔레그램 복약 알림 — 발송 (버튼 처리는 Cloudflare Worker Webhook)."""

from __future__ import annotations

import os

from src.medication_state import load_state, mark_morning_sent
from src.telegram_sender import send_medication_reminder


def deliver_morning(message: str) -> None:
    state = load_state()
    if state.get("morning_sent"):
        print("복약(텔레그램): 오늘 아침 알림 이미 발송함 — 건너뜀.")
        return
    if state.get("taken"):
        print("복약(텔레그램): 오늘 이미 복용 체크됨 — 건너뜀.")
        return

    message_id = send_medication_reminder(message)
    state = mark_morning_sent()
    state["telegram_message_id"] = message_id
    state["telegram_message_ids"] = [message_id]
    from src.medication_state import save_state

    save_state(state)

    if os.getenv("TELEGRAM_USE_WEBHOOK", "").strip() == "1":
        print("복약(텔레그램): Webhook 모드 — 버튼은 Worker가 즉시 처리합니다.")
