"""카카오톡 '나에게 보내기' — Gmail 확인 알림."""

from __future__ import annotations

import json
import os
from datetime import datetime

import requests

from src.kakao_oauth import kakao_client_fields

KAKAO_TOKEN_URL = "https://kauth.kakao.com/oauth/token"
KAKAO_MEMO_URL = "https://kapi.kakao.com/v2/api/talk/memo/default/send"
KAKAO_TEXT_MAX = 200
GMAIL_INBOX_URL = "https://mail.google.com/mail/u/0/#inbox"


def _require_env(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        raise ValueError(f"{name}를 .env 파일에 설정해 주세요.")
    return value


def get_access_token() -> str:
    _require_env("KAKAO_REST_API_KEY")
    refresh_token = _require_env("KAKAO_REFRESH_TOKEN")

    response = requests.post(
        KAKAO_TOKEN_URL,
        data={
            **kakao_client_fields(),
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
        },
        timeout=15,
    )
    response.raise_for_status()
    payload = response.json()

    new_refresh = payload.get("refresh_token")
    if new_refresh and new_refresh != refresh_token:
        print(
            "⚠️  카카오 refresh token이 갱신되었습니다. "
            ".env / GitHub Secret의 KAKAO_REFRESH_TOKEN을 업데이트하세요."
        )
        print(f"KAKAO_REFRESH_TOKEN={new_refresh}")

    return payload["access_token"]


def send_notification(email_to: str) -> None:
    """Gmail에서 전체 브리핑을 확인하라는 카카오 알림 1통."""
    access_token = get_access_token()
    today = datetime.now().strftime("%Y-%m-%d")
    text = (
        f"📋 취업 브리핑 ({today})\n\n"
        f"전체 뉴스·채용 공고는 Gmail로 보냈어요.\n"
        f"받은메일함({email_to})을 확인하세요."
    )
    if len(text) > KAKAO_TEXT_MAX:
        text = _truncate(text, KAKAO_TEXT_MAX)

    template = {
        "object_type": "text",
        "text": text,
        "link": {
            "web_url": GMAIL_INBOX_URL,
            "mobile_web_url": GMAIL_INBOX_URL,
        },
        "button_title": "Gmail 열기",
    }

    response = requests.post(
        KAKAO_MEMO_URL,
        headers={"Authorization": f"Bearer {access_token}"},
        data={"template_object": json.dumps(template, ensure_ascii=False)},
        timeout=15,
    )
    response.raise_for_status()
    print("카카오톡 알림 발송 완료 (Gmail 확인)")


def _truncate(text: str, max_len: int) -> str:
    if len(text) <= max_len:
        return text
    return text[: max_len - 1] + "…"
