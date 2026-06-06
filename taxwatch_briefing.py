#!/usr/bin/env python3
"""세금 뉴스 — TaxWatch + 이택스뉴스 당일 기사 Gmail 브리핑 + 텔레그램 알림."""

from __future__ import annotations

import sys
from pathlib import Path

import yaml
from dotenv import load_dotenv

from src.etaxnews_news import DEFAULT_FEEDS, fetch_today_by_section
from src.taxwatch_email_sender import send_digest as send_email_digest
from src.taxwatch_news import fetch_today_articles


def load_config() -> dict:
    config_path = Path(__file__).parent / "config.yaml"
    with config_path.open(encoding="utf-8") as f:
        return yaml.safe_load(f)


def _build_sections(config: dict) -> dict[str, list[dict]]:
    briefing_cfg = config.get("taxwatch_briefing", {})
    max_pages = int(briefing_cfg.get("max_pages") or 30)

    sections: dict[str, list[dict]] = {}

    if briefing_cfg.get("taxwatch", True):
        sections["TaxWatch"] = fetch_today_articles(max_pages=max_pages)

    etax_cfg = briefing_cfg.get("etaxnews") or {}
    if etax_cfg.get("enabled", True):
        feeds = etax_cfg.get("feeds") or DEFAULT_FEEDS
        for section_name, articles in fetch_today_by_section(
            feeds,
            max_pages=max_pages,
        ).items():
            sections[f"이택스뉴스 · {section_name}"] = articles

    return sections


def deliver_taxwatch_briefing() -> None:
    config = load_config()
    briefing_cfg = config.get("taxwatch_briefing", {})
    channel = (briefing_cfg.get("channel") or "telegram").strip().lower()

    print("1/2 세금 뉴스 수집 중...")
    sections = _build_sections(config)
    total = 0
    for section_name, articles in sections.items():
        print(f"  [{section_name}] {len(articles)}건")
        for article in articles:
            print(f"    • {article['title']}")
        total += len(articles)

    print("2/2 알림 발송 중...")
    email_to = send_email_digest(sections)
    print(f"Gmail 발송 완료 → {email_to}")

    if channel == "telegram":
        from src.telegram_sender import send_taxwatch_briefing_alert

        send_taxwatch_briefing_alert(email_to, total)
    elif channel == "kakao":
        raise ValueError(
            "taxwatch_briefing.channel=kakao 는 아직 지원하지 않습니다. telegram 을 사용해 주세요."
        )
    else:
        raise ValueError("taxwatch_briefing.channel은 telegram 이어야 합니다.")

    print("완료! Gmail 받은편지함을 확인해 주세요.")


def main() -> int:
    load_dotenv()
    try:
        deliver_taxwatch_briefing()
        return 0
    except Exception as exc:
        print(f"오류: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
