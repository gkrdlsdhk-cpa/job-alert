#!/usr/bin/env python3
"""매일 카카오톡으로 미국 주식 시세 알림 (기본: 테슬라, 엔비디아)."""

from __future__ import annotations

import sys
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import yaml
from dotenv import load_dotenv

from src.kakao_sender import send_stock_quotes_alert
from src.stock_quotes import fetch_quotes, format_kakao_body

KST = ZoneInfo("Asia/Seoul")


def load_config() -> dict:
    config_path = Path(__file__).parent / "config.yaml"
    with config_path.open(encoding="utf-8") as f:
        return yaml.safe_load(f)


def main() -> int:
    load_dotenv()
    config = load_config()
    stock_cfg = config.get("stock_alert", {})
    symbols = stock_cfg.get("symbols")
    if not symbols:
        raise ValueError("config.yaml의 stock_alert.symbols를 설정해 주세요.")

    now = datetime.now(KST)
    as_of = now.strftime("%m/%d %H:%M")

    print("주가 조회 중...")
    quotes = fetch_quotes(symbols)
    for q in quotes:
        sign = "+" if q.change_pct >= 0 else ""
        print(f"  {q.name}({q.symbol}) ${q.price:,.2f} {sign}{q.change_pct:.2f}%")

    body = format_kakao_body(quotes, as_of=as_of)
    print("카카오톡 발송 중...")
    send_stock_quotes_alert(body, link=quotes[0].link if quotes else None)
    print("완료!")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"오류: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
