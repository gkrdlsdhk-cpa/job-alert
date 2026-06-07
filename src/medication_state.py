"""복약 알림 — 당일 발송 상태."""

from __future__ import annotations

import json
import os
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

KST = ZoneInfo("Asia/Seoul")
DEFAULT_STATE_FILE = (
    Path(__file__).resolve().parent.parent / "data" / "medication_daily_state.json"
)


def _state_path() -> Path:
    raw = os.getenv("MEDICATION_DAILY_STATE_FILE", "").strip()
    return Path(raw) if raw else DEFAULT_STATE_FILE


def _today_kst() -> str:
    return datetime.now(KST).strftime("%Y-%m-%d")


def _empty_state() -> dict:
    return {
        "date": _today_kst(),
        "morning_sent": False,
    }


def load_state() -> dict:
    path = _state_path()
    today = _today_kst()
    if not path.exists():
        return _empty_state()
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return _empty_state()
    if data.get("date") != today:
        return _empty_state()
    return {**_empty_state(), **data, "date": today}


def save_state(state: dict) -> None:
    path = _state_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    state["date"] = _today_kst()
    path.write_text(json.dumps(state, ensure_ascii=False), encoding="utf-8")


def mark_morning_sent() -> dict:
    state = load_state()
    state["morning_sent"] = True
    save_state(state)
    return state
