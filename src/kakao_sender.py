"""카카오톡 '나에게 보내기' API로 브리핑을 전송합니다."""

from __future__ import annotations

import json
import os

import requests

from src.digest import build_text_lines, chunk_lines
from src.kakao_oauth import kakao_client_fields

KAKAO_TOKEN_URL = "https://kauth.kakao.com/oauth/token"
KAKAO_MEMO_URL = "https://kapi.kakao.com/v2/api/talk/memo/default/send"
KAKAO_TEXT_MAX = 200


def _require_env(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        raise ValueError(f"{name}를 .env 파일에 설정해 주세요.")
    return value


def get_access_token() -> str:
    """저장된 refresh token으로 access token을 발급합니다."""
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
            ".env의 KAKAO_REFRESH_TOKEN 값을 아래 새 값으로 바꿔 주세요."
        )
        print(f"KAKAO_REFRESH_TOKEN={new_refresh}")

    return payload["access_token"]


def send_text_message(access_token: str, text: str) -> None:
    if len(text) > KAKAO_TEXT_MAX:
        raise ValueError(f"카카오 메시지는 {KAKAO_TEXT_MAX}자 이하여야 합니다: {len(text)}자")

    template = {
        "object_type": "text",
        "text": text,
        "link": {
            "web_url": "https://www.naver.com",
            "mobile_web_url": "https://m.naver.com",
        },
        "button_title": "네이버",
    }

    response = requests.post(
        KAKAO_MEMO_URL,
        headers={"Authorization": f"Bearer {access_token}"},
        data={"template_object": json.dumps(template, ensure_ascii=False)},
        timeout=15,
    )
    response.raise_for_status()


def send_digest(
    company_news: dict[str, list[dict]],
    saramin_jobs: dict[str, list[dict]],
) -> None:
    access_token = get_access_token()
    lines = build_text_lines(company_news, saramin_jobs)
    messages = chunk_lines(lines)

    for message in messages:
        send_text_message(access_token, message)

    print(f"카카오톡 메시지 {len(messages)}건 전송 완료")
