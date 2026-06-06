#!/usr/bin/env python3
"""텔레그램 복용 버튼 실시간 감시 (long polling)."""

from __future__ import annotations

import argparse
import sys

from dotenv import load_dotenv


def main() -> int:
    parser = argparse.ArgumentParser(description="복용 완료 버튼 실시간 감시")
    parser.add_argument(
        "--max-minutes",
        type=int,
        default=180,
        help="최대 감시 시간(분). 기본 180분.",
    )
    parser.add_argument(
        "--exit-when-taken",
        action="store_true",
        help="복용 체크되면 감시 종료 (GitHub Actions용).",
    )
    parser.add_argument(
        "--require-morning-sent",
        action="store_true",
        help="오늘 아침 알림이 있을 때만 감시 (9시 워크플로용).",
    )
    parser.add_argument(
        "--require-followup-sent",
        action="store_true",
        help="오늘 후속 알림이 있을 때만 감시 (11시 워크플로용).",
    )
    args = parser.parse_args()

    load_dotenv()
    try:
        from src.medication_state import load_state
        from src.telegram_medication import watch_button_clicks

        state = load_state()
        if args.require_morning_sent and not state.get("morning_sent"):
            print("아침 알림 없음 — 감시 건너뜀.")
            return 0
        if args.require_followup_sent and not state.get("followup_sent"):
            print("후속 알림 없음 — 감시 건너뜀.")
            return 0
        if state.get("taken"):
            print("이미 복용 체크됨 — 감시 건너뜀.")
            return 0

        watch_button_clicks(
            max_minutes=args.max_minutes,
            exit_when_taken=args.exit_when_taken,
        )
        return 0
    except Exception as exc:
        print(f"오류: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
