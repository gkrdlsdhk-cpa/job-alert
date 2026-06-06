#!/usr/bin/env python3
"""복용 완료 체크 — 상태 파일에 기록."""

from __future__ import annotations

import sys

from dotenv import load_dotenv

from src.medication_state import load_state, mark_taken


def main() -> int:
    load_dotenv()
    try:
        state = mark_taken()
        print(f"복용 체크 완료: {state}")
        return 0
    except Exception as exc:
        print(f"오류: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
