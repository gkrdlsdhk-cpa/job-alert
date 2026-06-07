#!/usr/bin/env python3
"""사람인 채용 — 공고 검색 Gmail + 텔레그램 알림 (매일 12시)."""

from __future__ import annotations

import sys
from pathlib import Path

import yaml
from dotenv import load_dotenv

from src.email_sender import send_jobs_digest
from src.saramin_jobs import fetch_all_jobs


def load_config() -> dict:
    config_path = Path(__file__).parent / "config.yaml"
    with config_path.open(encoding="utf-8") as f:
        return yaml.safe_load(f)


def deliver_saramin_briefing() -> None:
    config = load_config()
    briefing_cfg = config.get("saramin_briefing") or {}
    channel = (briefing_cfg.get("channel") or "telegram").strip().lower()
    saramin_cfg = config.get("saramin") or {}

    print("1/2 사람인 채용 공고 수집 중...")
    saramin_jobs = fetch_all_jobs(
        keywords=saramin_cfg["search_keywords"],
        max_results_per_keyword=int(saramin_cfg.get("max_results_per_keyword", 5)),
    )
    job_count = 0
    for keyword, jobs in saramin_jobs.items():
        print(f"  [{keyword}] {len(jobs)}건")
        for job in jobs:
            print(f"    • {job['title']}")
        job_count += len(jobs)

    print("2/2 알림 발송 중...")
    email_to = send_jobs_digest(saramin_jobs)
    print(f"Gmail 발송 완료 → {email_to}")

    if channel == "telegram":
        from src.telegram_sender import send_saramin_briefing_alert

        send_saramin_briefing_alert(email_to, job_count)
    elif channel == "kakao":
        from src.kakao_sender import send_saramin_notification

        send_saramin_notification(email_to)
    elif channel == "email":
        pass
    else:
        raise ValueError(
            "saramin_briefing.channel은 telegram, kakao, email 중 하나여야 합니다."
        )

    print("완료! Gmail 받은편지함을 확인해 주세요.")


def main() -> int:
    load_dotenv()
    try:
        deliver_saramin_briefing()
        return 0
    except Exception as exc:
        print(f"오류: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
