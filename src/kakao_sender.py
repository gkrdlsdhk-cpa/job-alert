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
GMAIL_ICON_URL = "https://ssl.gstatic.com/ui/v1/icons/mail/rfr/gmail.ico"
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


def _build_feed_template(email_to: str, mail_url: str, today: str) -> dict:
    """피드 템플릿: 버튼/카드 클릭 시 Gmail 브리핑 검색으로 이동."""
    link = {"web_url": mail_url, "mobile_web_url": mail_url}
    return {
        "object_type": "feed",
        "content": {
            "title": f"📋 취업 브리핑 ({today})",
            "description": f"{email_to} 으로 전체 내용을 보냈어요.",
            "image_url": GMAIL_ICON_URL,
            "image_width": 64,
            "image_height": 64,
            "link": link,
        },
        "buttons": [
            {
                "title": "브리핑 메일 보기",
                "link": link,
            }
        ],
    }


def _send_text_template(access_token: str, text: str, link: str, button_title: str) -> None:
    if len(text) > KAKAO_TEXT_MAX:
        raise ValueError(f"카카오 메시지는 {KAKAO_TEXT_MAX}자 이하여야 합니다: {len(text)}자")

    web_link = {"web_url": link, "mobile_web_url": link}
    template = {
        "object_type": "text",
        "text": text,
        "link": web_link,
        "button_title": button_title,
    }
    response = requests.post(
        KAKAO_MEMO_URL,
        headers={"Authorization": f"Bearer {access_token}"},
        data={"template_object": json.dumps(template, ensure_ascii=False)},
        timeout=15,
    )
    response.raise_for_status()


def send_link_alert(
    prefix_line: str,
    title: str,
    link: str,
    *,
    button_title: str = "열기",
) -> None:
    """제목 + 링크 카카오 텍스트 메시지 (나에게 보내기)."""
    access_token = get_access_token()
    prefix = prefix_line if prefix_line.endswith("\n") else f"{prefix_line}\n"
    room = KAKAO_TEXT_MAX - len(prefix) - 1
    short_title = title
    if len(short_title) > room:
        short_title = short_title[: room - 1] + "…"
    text = f"{prefix}{short_title}"

    _send_text_template(access_token, text, link, button_title)
    print(f"카카오톡 알림 → {short_title}")


def send_kicpa_job_alert(title: str, link: str) -> None:
    """회계사회 신규 공고 — 제목 + 링크만 카카오톡으로 직접 전송."""
    send_link_alert("[회계사회 수습CPA 신규]", title, link, button_title="공고 보기")


def send_pwc_recruitment_alert(title: str, link: str) -> None:
    """삼일PwC 정기채용 모집 오픈 — 제목 + 링크."""
    send_link_alert("[삼일PwC 정기채용]", title, link, button_title="채용 보기")


def send_notification(email_to: str) -> None:
    """Gmail 브리핑 링크가 포함된 카카오 알림 1통."""
    access_token = get_access_token()
    today = datetime.now().strftime("%Y-%m-%d")
    mail_url = gmail_briefing_url(email_to)
    template = _build_feed_template(email_to, mail_url, today)

    response = requests.post(
        KAKAO_MEMO_URL,
        headers={"Authorization": f"Bearer {access_token}"},
        data={"template_object": json.dumps(template, ensure_ascii=False)},
        timeout=15,
    )
    response.raise_for_status()
    print(f"카카오톡 알림 발송 완료 → {mail_url}")
    print(
        "⚠️  버튼이 안 열리면 카카오 개발자 → 제품 링크 관리 → 웹 도메인에 "
        "https://mail.google.com 을 등록했는지 확인하세요."
    )
