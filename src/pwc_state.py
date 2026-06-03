"""삼일PwC 정기채용 모집 오픈 알림 상태."""

from __future__ import annotations

import json
import os
from pathlib import Path

DEFAULT_STATE_PATH = Path(__file__).resolve().parent.parent / "data" / "pwc_graduate_state.json"


def state_path() -> Path:
    custom = os.getenv("PWC_STATE_FILE", "").strip()
    return Path(custom) if custom else DEFAULT_STATE_PATH


def load_state() -> dict:
    path = state_path()
    if not path.is_file():
        return {"initialized": False, "notified_open": False, "last_open": False, "fingerprint": ""}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {"initialized": False, "notified_open": False, "last_open": False, "fingerprint": ""}
    data.setdefault("initialized", False)
    data.setdefault("notified_open", False)
    data.setdefault("last_open", False)
    data.setdefault("fingerprint", "")
    return data


def save_state(state: dict) -> None:
    path = state_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "initialized": bool(state.get("initialized")),
        "notified_open": bool(state.get("notified_open")),
        "last_open": bool(state.get("last_open")),
        "fingerprint": str(state.get("fingerprint", "")),
    }
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
