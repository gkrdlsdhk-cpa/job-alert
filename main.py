#!/usr/bin/env python3
"""매일 실행할 메인 스크립트: 뉴스 + 사람인 채용 → 이메일/카카오톡 발송."""

from __future__ import annotations

import os
import sys
from pathlib import Path

import yaml
from dotenv import load_dotenv

from src.email_sender import send_digest as send_email_digest
from src.kakao_sender import send_digest as send_kakao_digest
from src.naver_news import fetch_company_news
from src.saramin_jobs import fetch_all_jobs


def load_config() -> dict:
    config_path = Path(__file__).parent / "config.yaml"
    with config_path.open(encoding="utf-8") as f:
        return yaml.safe_load(f)


def main() -> int:
    load_dotenv()
    config = load_config()

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
    notify_via = os.getenv("NOTIFY_VIA", "email").strip().lower()

    if notify_via in {"email", "both"}:
        send_email_digest(company_news, saramin_jobs)
        print("이메일 발송 완료")

    if notify_via in {"kakao", "both"}:
        send_kakao_digest(company_news, saramin_jobs)

    if notify_via not in {"email", "kakao", "both"}:
        raise ValueError("NOTIFY_VIA는 email, kakao, both 중 하나여야 합니다.")

    print("완료! 메일함 또는 카카오톡 '나와의 채팅'을 확인해 주세요.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"오류: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
