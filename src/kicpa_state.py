"""회계사회 실시간 알림 — 이미 보낸 공고 ID 저장."""

from __future__ import annotations

import json
import os
from pathlib import Path

DEFAULT_STATE_PATH = Path(__file__).resolve().parent.parent / "data" / "kicpa_notified.json"
MAX_STORED_IDS = 400


def state_path() -> Path:
    custom = os.getenv("KICPA_STATE_FILE", "").strip()
    return Path(custom) if custom else DEFAULT_STATE_PATH


def load_state() -> dict:
    path = state_path()
    if not path.is_file():
        # 상태 파일 없음(캐시 미복구 등) — 재-seed 시 신규 공고까지 알림 누락 방지
        return {"initialized": True, "notified_ids": [], "needs_baseline": True}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {"initialized": True, "notified_ids": [], "needs_baseline": True}
    if not isinstance(data.get("notified_ids"), list):
        data["notified_ids"] = []
    data.setdefault("initialized", True)
    data.setdefault("needs_baseline", False)
    return data


def save_state(state: dict) -> None:
    path = state_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    ids = [str(i) for i in state.get("notified_ids", []) if i]
    if len(ids) > MAX_STORED_IDS:
        ids = ids[-MAX_STORED_IDS:]
    payload = {
        "initialized": True,
        "notified_ids": ids,
    }
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def notified_id_set(state: dict) -> set[str]:
    return {str(i) for i in state.get("notified_ids", []) if i}
