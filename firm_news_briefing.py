#!/usr/bin/env python3
"""회계법인 뉴스 — 네이버 뉴스 당일 기사 Gmail + 텔레그램 알림 (매일 23시)."""

from __future__ import annotations

import sys
from pathlib import Path

import yaml
from dotenv import load_dotenv

from src.email_sender import send_news_digest
from src.naver_news import fetch_company_news


def load_config() -> dict:
    config_path = Path(__file__).parent / "config.yaml"
    with config_path.open(encoding="utf-8") as f:
        return yaml.safe_load(f)


def deliver_firm_news_briefing() -> None:
    config = load_config()
    briefing_cfg = config.get("firm_news_briefing") or {}
    channel = (briefing_cfg.get("channel") or "telegram").strip().lower()
    naver_cfg = config.get("naver") or {}

    print("1/2 회계법인 뉴스 수집 중...")
    company_news = fetch_company_news(
        companies=config["companies"],
        max_fetch_per_keyword=int(naver_cfg.get("max_fetch_per_keyword", 50)),
        today_only=bool(naver_cfg.get("today_only", True)),
        sort=str(naver_cfg.get("sort", "date")),
    )
    news_count = 0
    for company, articles in company_news.items():
        print(f"  [{company}] {len(articles)}건")
        for article in articles:
            print(f"    • {article['title']}")
        news_count += len(articles)

    print("2/2 알림 발송 중...")
    email_to = send_news_digest(company_news)
    print(f"Gmail 발송 완료 → {email_to}")

    if channel == "telegram":
        from src.telegram_sender import send_firm_news_briefing_alert

        send_firm_news_briefing_alert(email_to, news_count)
    elif channel == "kakao":
        from src.kakao_sender import send_firm_news_notification

        send_firm_news_notification(email_to)
    elif channel == "email":
        pass
    else:
        raise ValueError(
            "firm_news_briefing.channel은 telegram, kakao, email 중 하나여야 합니다."
        )

    print("완료! Gmail 받은편지함을 확인해 주세요.")


def main() -> int:
    load_dotenv()
    try:
        deliver_firm_news_briefing()
        return 0
    except Exception as exc:
        print(f"오류: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
