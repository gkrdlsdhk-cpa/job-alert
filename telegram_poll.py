#!/usr/bin/env python3
"""텔레그램 복용 완료 버튼 클릭 수신 (getUpdates 폴링)."""

from __future__ import annotations

import sys

from dotenv import load_dotenv


def main() -> int:
    load_dotenv()
    try:
        from src.telegram_medication import poll_button_clicks

        count = poll_button_clicks()
        if count:
            print(f"처리 완료: {count}건")
        else:
            print("새 버튼 클릭 없음.")
        return 0
    except Exception as exc:
        print(f"오류: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
