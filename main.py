#!/usr/bin/env python3
"""매일 실행: 뉴스 + 채용 수집 → Gmail 전체 브리핑 (+ 선택: 카카오 알림)."""

from __future__ import annotations

import os
import sys
from pathlib import Path

import yaml
from dotenv import load_dotenv

from src.email_sender import send_digest as send_email_digest
from src.kakao_sender import send_notification as send_kakao_notification
from src.naver_news import fetch_company_news
from src.saramin_jobs import fetch_all_jobs


def load_config() -> dict:
    config_path = Path(__file__).parent / "config.yaml"
    with config_path.open(encoding="utf-8") as f:
        return yaml.safe_load(f)


def main() -> int:
    load_dotenv()
    config = load_config()
    notify_via = os.getenv("NOTIFY_VIA", "both").strip().lower()

    print("1/3 네이버 뉴스 수집 중...")
    company_news = fetch_company_news(
        companies=config["companies"],
        news_per_keyword=config["naver"]["news_per_keyword"],
    )

    print("2/3 사람인 채용 공고 수집 중...")
    saramin_jobs = fetch_all_jobs(
        keywords=config["saramin"]["search_keywords"],
        max_results_per_keyword=config["saramin"]["max_results_per_keyword"],
    )

    print("3/3 알림 발송 중...")
    email_to = send_email_digest(company_news, saramin_jobs)
    print(f"Gmail 발송 완료 → {email_to}")

    if notify_via in {"kakao", "both"}:
        send_kakao_notification(email_to)
    elif notify_via != "email":
        raise ValueError("NOTIFY_VIA는 email, kakao, both 중 하나여야 합니다.")

    print("완료! Gmail 받은편지함을 확인해 주세요.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"오류: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
