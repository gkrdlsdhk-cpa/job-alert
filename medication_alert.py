#!/usr/bin/env python3
"""매일 복약 알림 (텔레그램 또는 카카오)."""

from __future__ import annotations

import sys
from pathlib import Path

import yaml
from dotenv import load_dotenv


def load_config() -> dict:
    config_path = Path(__file__).parent / "config.yaml"
    with config_path.open(encoding="utf-8") as f:
        return yaml.safe_load(f)


def deliver_medication_alert() -> None:
    config = load_config()
    med_cfg = config.get("medication_alert", {})
    channel = (med_cfg.get("channel") or "telegram").strip().lower()
    message = (med_cfg.get("message") or "아침 약 드실 시간이에요.").strip()

    if channel == "telegram":
        from src.telegram_medication import deliver_morning

        deliver_morning(message)
        return

    if channel == "kakao":
        from src.kakao_sender import send_medication_alert
        from src.medication_state import load_state, mark_morning_sent

        state = load_state()
        if state.get("morning_sent"):
            print("복약알림: 오늘 아침 알림 이미 발송함 — 건너뜀.")
            return
        if state.get("taken"):
            print("복약알림: 오늘 이미 복용 체크됨 — 건너뜀.")
            return

        mark_url = (med_cfg.get("mark_taken_url") or "").strip()
        if not mark_url:
            raise ValueError("카카오 모드: medication_alert.mark_taken_url 설정 필요 (§9 GAS)")

        send_medication_alert(message, mark_taken_url=mark_url)
        mark_morning_sent()
        print("완료!")
        return

    raise ValueError("medication_alert.channel은 telegram 또는 kakao 여야 합니다.")


def main() -> int:
    load_dotenv()
    try:
        deliver_medication_alert()
        return 0
    except Exception as exc:
        print(f"오류: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
