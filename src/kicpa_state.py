"""회계사회 실시간 알림 — 공고별 job_id + 제목 + 등록일 스냅샷."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Callable

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
    return f"{title}|{date}" if date else title


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


def _mark_notified(notified: dict[str, list[str]], job_id: str, fp: str) -> None:
    if not fp:
        return
    items = notified.setdefault(job_id, [])
    if fp not in items:
        items.append(fp)
    if len(items) > 10:
        notified[job_id] = items[-10:]


def _already_notified(notified: dict[str, list[str]], job_id: str, fp: str) -> bool:
    return fp in notified.get(job_id, [])


def _normalize_fp(fp: str) -> str:
    return fp


def load_notified_fingerprints(
    data: dict,
    snapshots: dict[str, str],
    *,
    normalize_func: Callable[[str], str] = _normalize_fp,
) -> dict[str, list[str]]:
    """저장된 알림 이력 로드. 없으면 현재 스냅샷을 이미 알림 보낸 것으로 간주."""
    raw = data.get("notified_fingerprints")
    if isinstance(raw, dict) and raw:
        notified: dict[str, list[str]] = {}
        for job_id, fps in raw.items():
            if not job_id or not isinstance(fps, list):
                continue
            cleaned = [normalize_func(str(fp)) for fp in fps if fp]
            cleaned = [fp for fp in cleaned if fp]
            if cleaned:
                notified[str(job_id)] = list(dict.fromkeys(cleaned))  # dedupe
        return notified

    notified = {}
    for job_id, fp in snapshots.items():
        if fp and fp != LEGACY_MARKER:
            _mark_notified(notified, str(job_id), normalize_func(str(fp)))
    return notified


def _is_title_only_upgrade(old: str, new: str) -> bool:
    """최근 title-only 저장값을 title|date로 되돌릴 때 기존 공고 재알림을 막음."""
    return bool(old and "|" not in old and new.startswith(f"{old}|"))


def load_state() -> dict:
    path = state_path()
    if not path.is_file():
        return {
            "initialized": True,
            "job_snapshots": {},
            "notified_fingerprints": {},
            "needs_baseline": True,
        }
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {
            "initialized": True,
            "job_snapshots": {},
            "notified_fingerprints": {},
            "needs_baseline": True,
        }

    snapshots = _migrate_legacy(data)
    return {
        "initialized": True,
        "job_snapshots": snapshots,
        "notified_fingerprints": load_notified_fingerprints(data, snapshots),
        "needs_baseline": bool(data.get("needs_baseline", False)),
        "board_baselines": data.get("board_baselines", {}),
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
    snapshots = dict(items)

    notified = state.get("notified_fingerprints", {})
    if not isinstance(notified, dict):
        notified = {}
    trimmed_notified = {
        job_id: notified[job_id]
        for job_id in snapshots
        if job_id in notified and notified[job_id]
    }

    payload = {
        "initialized": True,
        "job_snapshots": snapshots,
        "notified_fingerprints": trimmed_notified,
        "board_baselines": state.get("board_baselines", {}),
    }
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def apply_jobs_to_snapshots(
    jobs: list[dict],
    snapshots: dict[str, str],
    notified: dict[str, list[str]],
    *,
    baseline: bool = False,
    fingerprint_func: Callable[[dict], str] = job_fingerprint,
    migrate_title_only_without_notify: bool = True,
) -> tuple[list[tuple[dict, str]], dict[str, str], dict[str, list[str]]]:
    """
    공고 목록과 스냅샷을 비교합니다.

    같은 job_id라도 fingerprint(제목·등록일)가 바뀌면 수정·재게시 알림 —
    단, 그 fingerprint로는 이미 알림을 보낸 적 없을 때만 1회 발송.
    """
    updated = dict(snapshots)
    notified_updated = {k: list(v) for k, v in notified.items()}
    to_notify: list[tuple[dict, str]] = []

    for job in jobs:
        job_id = str(job.get("job_id", "")).strip()
        if not job_id:
            continue
        fp = fingerprint_func(job)
        old = updated.get(job_id)

        if baseline:
            updated[job_id] = fp
            _mark_notified(notified_updated, job_id, fp)
            continue

        if old is None:
            if not _already_notified(notified_updated, job_id, fp):
                to_notify.append((job, "신규"))
            updated[job_id] = fp
            _mark_notified(notified_updated, job_id, fp)
        elif old == LEGACY_MARKER:
            updated[job_id] = fp
            _mark_notified(notified_updated, job_id, fp)
        elif old != fp:
            updated[job_id] = fp
            if migrate_title_only_without_notify and _is_title_only_upgrade(old, fp):
                _mark_notified(notified_updated, job_id, fp)
                continue
            if not _already_notified(notified_updated, job_id, fp):
                to_notify.append((job, "수정·재게시"))
            _mark_notified(notified_updated, job_id, fp)

    return to_notify, updated, notified_updated
