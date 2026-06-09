#!/usr/bin/env python3
"""레거시 진입점 — firm_news_briefing.py 로 분리되었습니다."""

from __future__ import annotations

import sys


def main() -> int:
    print(
        "main.py는 더 이상 통합 브리핑을 실행하지 않습니다.\n"
        "  • 회계법인 뉴스 (23시): python firm_news_briefing.py",
        file=sys.stderr,
    )
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
