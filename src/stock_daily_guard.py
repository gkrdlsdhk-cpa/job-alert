"""9시 주가보고 — 하루 1회만 발송."""

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

