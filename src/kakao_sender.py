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


def gmail_briefing_url(email_to: str, *, mail_subject: str | None = None) -> str:
    """본인 Gmail 계정에서 브리핑 메일 검색 화면으로 연결."""
    today = datetime.now().strftime("%Y-%m-%d")
    authuser = quote(email_to, safe="")
    query = quote(mail_subject or f"[취업 브리핑] {today}", safe="")
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


def send_saramin_job_alert(company: str, title: str, link: str) -> None:
    """사람인 Big4 신규 공고 — 제목 + 링크."""
    send_link_alert(f"[사람인 {company}]", title, link, button_title="공고 보기")


def send_kpmg_career_alert(title: str, link: str) -> None:
    """삼정 KPMG 채용 사이트 신입 공고 — 제목 + 링크."""
    send_link_alert("[삼정KPMG 신입]", title, link, button_title="채용 보기")


def send_ey_career_alert(title: str, link: str) -> None:
    """EY한영(한영회계법인) 채용 사이트 수시 — 제목 + 링크."""
    send_link_alert("[EY한영 수시]", title, link, button_title="공고 보기")


def send_deloitte_career_alert(title: str, link: str) -> None:
    """딜로이트 채용 — 신입·Tax & Legal 검색 결과."""
    send_link_alert("[딜로이트 Tax&Legal]", title, link, button_title="공고 보기")


def send_pwc_recruitment_alert(title: str, link: str) -> None:
    """삼일PwC 정기채용 모집 오픈 — 제목 + 링크."""
    send_link_alert("[삼일PwC 정기채용]", title, link, button_title="채용 보기")


def send_khubiz_notice_alert(title: str, link: str) -> None:
    """경희대 경영대학 공지사항 — 채용 키워드 공지."""
    send_link_alert("[경희대 경영대학 공지]", title, link, button_title="공지 보기")


def _github_actions_run_url() -> str:
    server = os.getenv("GITHUB_SERVER_URL", "").strip().rstrip("/")
    repository = os.getenv("GITHUB_REPOSITORY", "").strip()
    run_id = os.getenv("GITHUB_RUN_ID", "").strip()
    if server and repository and run_id:
        return f"{server}/{repository}/actions/runs/{run_id}"
    if repository:
        return f"https://github.com/{repository}/actions"
    return "https://github.com/gkrdlsdhk-cpa/job-alert/actions"


_WATCH_FRIENDLY_NAMES = {
    "회계사회": "회계사회",
    "삼일PwC": "삼일PwC",
    "사람인 Big4": "사람인",
    "삼정KPMG": "삼정KPMG",
    "EY한영": "EY한영",
    "딜로이트": "딜로이트",
    "경희대 경영대학": "경희대 경영대학",
}


def _watch_friendly_name(label: str) -> str:
    return _WATCH_FRIENDLY_NAMES.get(label, label)


def _short_error_message(error: str, *, max_len: int = 60) -> str:
    err = error.replace("\n", " ").strip()
    if len(err) > max_len:
        return err[: max_len - 1] + "…"
    return err


def _join_korean_names(names: list[str]) -> str:
    if len(names) == 1:
        return names[0]
    if len(names) == 2:
        return f"{names[0]}, {names[1]}"
    return ", ".join(names[:-1]) + f", {names[-1]}"


def _format_watch_failure_summary(
    failures: list[tuple[int, str, str]],
    *,
    total_steps: int,
) -> str:
    """카카오 200자 제한 안에서 직관적인 실패 안내 문장."""
    del total_steps  # 호출부 호환용

    names = [_watch_friendly_name(label) for _, label, _ in failures]
    joined = _join_korean_names(names)
    headline = f"{joined}에서 확인에 실패했어요."

    if len(failures) == 1:
        err = _short_error_message(failures[0][2])
        body = f"{headline}\n{err}" if err else headline
    else:
        detail_lines = [
            f"· {_watch_friendly_name(label)}: {_short_error_message(error, max_len=40)}"
            for _, label, error in failures
        ]
        body = headline + "\n" + "\n".join(detail_lines)

    prefix = "[Job Alert 오류]\n"
    max_body = KAKAO_TEXT_MAX - len(prefix) - 1
    if len(body) <= max_body:
        return body

    if len(failures) == 1:
        room = max_body - len(headline) - 1
        if room > 10:
            err = _short_error_message(failures[0][2], max_len=room)
            return f"{headline}\n{err}" if err else headline
        return headline[:max_body]

    return headline[:max_body]


def send_realtime_watch_failure_alert(
    failures: list[tuple[int, str, str]],
    *,
    total_steps: int,
) -> None:
    """Realtime Job Alerts watch step 실패 요약 — 카카오 알림."""
    summary = _format_watch_failure_summary(failures, total_steps=total_steps)
    send_link_alert(
        "[Job Alert 오류]",
        summary,
        _github_actions_run_url(),
        button_title="Actions 로그",
    )


def send_stock_quotes_alert(body: str, *, link: str | None = None) -> None:
    """테슬라·엔비디아 등 미국 주식 시세 — 나에게 보내기."""
    send_link_alert(
        "<주가보고>",
        body,
        link or "https://m.stock.naver.com/worldstock/home",
        button_title="네이버 증권",
    )


def send_firm_news_notification(email_to: str) -> None:
    """회계법인 뉴스 Gmail 확인 카카오 알림."""
    today = datetime.now().strftime("%Y-%m-%d")
    mail_url = gmail_briefing_url(email_to, mail_subject=f"[회계법인 뉴스] {today}")
    _send_feed_alert(
        email_to,
        mail_url,
        today,
        card_title=f"📰 회계법인 뉴스 ({today})",
    )


def send_notification(email_to: str) -> None:
    """레거시: 통합 취업 브리핑 Gmail 확인 카카오 알림."""
    today = datetime.now().strftime("%Y-%m-%d")
    mail_url = gmail_briefing_url(email_to, mail_subject=f"[취업 브리핑] {today}")
    _send_feed_alert(
        email_to,
        mail_url,
        today,
        card_title=f"📋 취업 브리핑 ({today})",
    )


def _send_feed_alert(
    email_to: str, mail_url: str, today: str, *, card_title: str
) -> None:
    access_token = get_access_token()
    link = {"web_url": mail_url, "mobile_web_url": mail_url}
    template = {
        "object_type": "feed",
        "content": {
            "title": card_title,
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
