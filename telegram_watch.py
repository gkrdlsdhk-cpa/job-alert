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
    args = parser.parse_args()

    load_dotenv()
    try:
        from src.telegram_medication import watch_button_clicks

        watch_button_clicks(max_minutes=args.max_minutes)
        return 0
    except Exception as exc:
        print(f"오류: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
