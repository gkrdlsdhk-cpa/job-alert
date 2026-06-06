"""텔레그램 봇 API — 복약 알림·인라인 버튼."""

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


def send_medication_reminder(text: str) -> int:
    """복약 알림 + 「먹었어요 ✅」 버튼. 누르면 메시지가 복용 완료로 바뀜."""
    response = requests.post(
        _api_url("sendMessage"),
        json={
            "chat_id": _chat_id(),
            "text": f"💊 {text}",
            "reply_markup": {
                "inline_keyboard": [
                    [{"text": "먹었어요 ✅", "callback_data": CALLBACK_MED_TAKEN}]
                ]
            },
        },
        timeout=15,
    )
    response.raise_for_status()
    payload = response.json()
    if not payload.get("ok"):
        raise RuntimeError(f"텔레그램 발송 실패: {payload}")
    message_id = payload["result"]["message_id"]
    print(f"텔레그램 발송 완료 (message_id={message_id})")
    return message_id


def get_updates(*, offset: int | None = None, timeout: int = 0) -> list[dict]:
    params: dict = {"timeout": timeout}
    if timeout > 0:
        params["allowed_updates"] = ["callback_query"]
    if offset is not None:
        params["offset"] = offset
    response = requests.get(
        _api_url("getUpdates"),
        params=params,
        timeout=max(15, timeout + 5),
    )
    response.raise_for_status()
    payload = response.json()
    if not payload.get("ok"):
        raise RuntimeError(f"getUpdates 실패: {payload}")
    return payload.get("result", [])


def answer_callback(callback_query_id: str, text: str = "복용 완료!") -> bool:
    """버튼 탭 확인. 만료된 클릭(400)은 False, 성공 시 True."""
    response = requests.post(
        _api_url("answerCallbackQuery"),
        json={"callback_query_id": callback_query_id, "text": text},
        timeout=15,
    )
    if response.status_code == 400:
        return False
    response.raise_for_status()
    return True


def mark_message_taken(chat_id: str | int, message_id: int, *, original_text: str) -> None:
    """버튼 누른 뒤 메시지에 체크 표시."""
    response = requests.post(
        _api_url("editMessageText"),
        json={
            "chat_id": chat_id,
            "message_id": message_id,
            "text": f"✅ {original_text}\n\n복용 완료",
            "reply_markup": {"inline_keyboard": []},
        },
        timeout=15,
    )
    response.raise_for_status()
