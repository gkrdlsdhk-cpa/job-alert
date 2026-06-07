"""삼정 KPMG 실시간 알림 — 공고별 jobopen_id + 제목 + 마감일 스냅샷."""

from __future__ import annotations

import json
import os
from pathlib import Path

from src.kicpa_state import apply_jobs_to_snapshots, job_fingerprint

DEFAULT_STATE_PATH = (
    Path(__file__).resolve().parent.parent / "data" / "kpmg_notified.json"
)


def state_path() -> Path:
    custom = os.getenv("KPMG_STATE_FILE", "").strip()
    return Path(custom) if custom else DEFAULT_STATE_PATH


def load_state() -> dict:
    path = state_path()
    if not path.is_file():
        return {
            "initialized": True,
            "job_snapshots": {},
            "needs_baseline": True,
        }
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {
            "initialized": True,
            "job_snapshots": {},
            "needs_baseline": True,
        }

    snapshots = data.get("job_snapshots", {})
    if not isinstance(snapshots, dict):
        snapshots = {}
    return {
        "initialized": True,
        "job_snapshots": {str(k): str(v) for k, v in snapshots.items() if k and v},
        "needs_baseline": bool(data.get("needs_baseline", False)),
    }


def save_state(state: dict) -> None:
    path = state_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    snapshots = state.get("job_snapshots", {})
    if not isinstance(snapshots, dict):
        snapshots = {}
    payload = {
        "initialized": True,
        "job_snapshots": {str(k): str(v) for k, v in snapshots.items() if k and v},
    }
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


__all__ = [
    "apply_jobs_to_snapshots",
    "job_fingerprint",
    "load_state",
    "save_state",
]
