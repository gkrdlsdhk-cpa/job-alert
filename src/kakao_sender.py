"""카카오톡 '나에게 보내기' — Gmail 확인 알림."""

from __future__ import annotations

import json
import os
from datetime import datetime
from urllib.parse import quote

import requests

from src.kakao_oauth import kakao_client_fields

KAKAO_TOKEN_URL = "https://kauth.kakao.com/oauth/token"
KAKAO_MEMO_URL = "https://kapi.kakao.com/v2/api/talk/memo/default/send"
KAKAO_TEXT_MAX = 200


def gmail_briefing_url(email_to: str) -> str:
    """본인 Gmail 계정에서 오늘 브리핑 메일 검색 화면으로 연결."""
    today = datetime.now().strftime("%Y-%m-%d")
    authuser = quote(email_to, safe="")
    query = quote(f"[취업 브리핑] {today}", safe="")
    return f"https://mail.google.com/mail/?authuser={authuser}#search/{query}"


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
    mail_url = gmail_briefing_url(email_to)
    text = (
        f"📋 취업 브리핑 ({today})\n\n"
        f"전체 내용은 {email_to} 으로 보냈어요.\n"
        "아래 버튼을 누르면 브리핑 메일로 바로 이동해요."
    )
    if len(text) > KAKAO_TEXT_MAX:
        text = _truncate(text, KAKAO_TEXT_MAX)

    template = {
        "object_type": "text",
        "text": text,
        "link": {
            "web_url": mail_url,
            "mobile_web_url": mail_url,
        },
        "button_title": "브리핑 메일 보기",
    }

    response = requests.post(
        KAKAO_MEMO_URL,
        headers={"Authorization": f"Bearer {access_token}"},
        data={"template_object": json.dumps(template, ensure_ascii=False)},
        timeout=15,
    )
    response.raise_for_status()
    print(f"카카오톡 알림 발송 완료 → {mail_url}")


def _truncate(text: str, max_len: int) -> str:
    if len(text) <= max_len:
        return text
    return text[: max_len - 1] + "…"
