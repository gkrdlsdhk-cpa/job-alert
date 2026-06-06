#!/usr/bin/env python3
"""복용 체크 없을 때 후속 알림 (텔레그램 또는 카카오)."""

from __future__ import annotations

import sys
from pathlib import Path

import yaml
from dotenv import load_dotenv


def load_config() -> dict:
    config_path = Path(__file__).parent / "config.yaml"
    with config_path.open(encoding="utf-8") as f:
        return yaml.safe_load(f)


def deliver_medication_followup() -> None:
    config = load_config()
    med_cfg = config.get("medication_alert", {})
    channel = (med_cfg.get("channel") or "telegram").strip().lower()
    message = (
        med_cfg.get("follow_up_message")
        or "아직 복용 체크가 없어요. 아래 버튼을 눌러 주세요."
    ).strip()

    if channel == "telegram":
        from src.telegram_medication import deliver_followup

        deliver_followup(message)
        return

    if channel == "kakao":
        from src.kakao_sender import send_medication_alert
        from src.medication_state import load_state, mark_followup_sent

        state = load_state()
        if not state.get("morning_sent"):
            print("복약 후속: 오늘 아침 알림 없음 — 건너뜀.")
            return
        if state.get("taken"):
            print("복약 후속: 이미 복용 체크됨 — 건너뜀.")
            return
        if state.get("followup_sent"):
            print("복약 후속: 오늘 후속 알림 이미 발송함 — 건너뜀.")
            return

        mark_url = (med_cfg.get("mark_taken_url") or "").strip()
        if not mark_url:
            raise ValueError("카카오 모드: medication_alert.mark_taken_url 설정 필요")

        send_medication_alert(message, mark_taken_url=mark_url)
        mark_followup_sent()
        print("완료!")
        return

    raise ValueError("medication_alert.channel은 telegram 또는 kakao 여야 합니다.")


def main() -> int:
    load_dotenv()
    try:
        deliver_medication_followup()
        return 0
    except Exception as exc:
        print(f"오류: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
