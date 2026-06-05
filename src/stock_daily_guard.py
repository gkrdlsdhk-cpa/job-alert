"""9시 주가보고 — 하루 1회만 발송 (KICPA 워크플로 백업용)."""

from __future__ import annotations

import json
import os
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

KST = ZoneInfo("Asia/Seoul")
DEFAULT_STATE_FILE = Path(__file__).resolve().parent.parent / "data" / "stock_daily_sent.json"


def _state_path() -> Path:
    raw = os.getenv("STOCK_DAILY_STATE_FILE", "").strip()
    return Path(raw) if raw else DEFAULT_STATE_FILE


def _today_kst() -> str:
    return datetime.now(KST).strftime("%Y-%m-%d")


def already_sent_today() -> bool:
    path = _state_path()
    if not path.exists():
        return False
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return False
    return data.get("last_sent_date") == _today_kst()


def mark_sent_today() -> None:
    path = _state_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps({"last_sent_date": _today_kst()}, ensure_ascii=False),
        encoding="utf-8",
    )


def maybe_send_morning_stock_alert() -> bool:
    """KST 9시대(9~9:59)이고 오늘 아직 안 보냈으면 주가보고 발송."""
    if datetime.now(KST).hour != 9:
        return False
    if already_sent_today():
        print("주가보고: 오늘 이미 발송함 — 건너뜀.")
        return False

    from stock_alert import deliver_stock_alert

    print("주가보고: 9시 백업 발송 시도 (Realtime Job Alerts)...")
    deliver_stock_alert()
    mark_sent_today()
    return True
