"""회계사회 실시간 알림 — 공고별 job_id + 제목 + 등록일 스냅샷."""

from __future__ import annotations

import json
import os
from pathlib import Path

DEFAULT_STATE_PATH = Path(__file__).resolve().parent.parent / "data" / "kicpa_notified.json"
MAX_STORED_JOBS = 400
LEGACY_MARKER = "__legacy__"


def state_path() -> Path:
    custom = os.getenv("KICPA_STATE_FILE", "").strip()
    return Path(custom) if custom else DEFAULT_STATE_PATH


def job_fingerprint(job: dict) -> str:
    """제목·등록일이 바뀌면 값이 달라짐."""
    title = str(job.get("title", "")).strip()
    date = str(job.get("date", "")).strip()
    return f"{title}|{date}"


def _migrate_legacy(data: dict) -> dict[str, str]:
    """예전 notified_ids 형식 → job_snapshots."""
    snapshots: dict[str, str] = {}
    if isinstance(data.get("job_snapshots"), dict):
        for job_id, fp in data["job_snapshots"].items():
            if job_id:
                snapshots[str(job_id)] = str(fp)
    legacy_ids = data.get("notified_ids") or []
    if isinstance(legacy_ids, list):
        for job_id in legacy_ids:
            if job_id and str(job_id) not in snapshots:
                snapshots[str(job_id)] = LEGACY_MARKER
    return snapshots


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

    snapshots = _migrate_legacy(data)
    return {
        "initialized": True,
        "job_snapshots": snapshots,
        "needs_baseline": bool(data.get("needs_baseline", False)),
    }


def save_state(state: dict) -> None:
    path = state_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    snapshots = state.get("job_snapshots", {})
    if not isinstance(snapshots, dict):
        snapshots = {}
    items = [(str(k), str(v)) for k, v in snapshots.items() if k and v]
    if len(items) > MAX_STORED_JOBS:
        items = items[-MAX_STORED_JOBS:]
    payload = {
        "initialized": True,
        "job_snapshots": dict(items),
    }
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def apply_jobs_to_snapshots(
    jobs: list[dict],
    snapshots: dict[str, str],
    *,
    baseline: bool = False,
) -> tuple[list[tuple[dict, str]], dict[str, str]]:
    """
    공고 목록과 스냅샷을 비교합니다.

    반환: (알림 대상 [(job, 사유), ...], 갱신된 스냅샷)
    """
    updated = dict(snapshots)
    to_notify: list[tuple[dict, str]] = []

    for job in jobs:
        job_id = str(job.get("job_id", "")).strip()
        if not job_id:
            continue
        fp = job_fingerprint(job)
        old = updated.get(job_id)

        if baseline:
            updated[job_id] = fp
            continue

        if old is None:
            to_notify.append((job, "신규"))
            updated[job_id] = fp
        elif old == LEGACY_MARKER:
            updated[job_id] = fp
        elif old != fp:
            to_notify.append((job, "수정·재게시"))
            updated[job_id] = fp

    return to_notify, updated
