"""사람인 실시간 알림 — 공고별 rec_idx + 제목 + 마감일 스냅샷."""

from __future__ import annotations

import json
import os
from pathlib import Path

from src.kicpa_state import (
    apply_jobs_to_snapshots as _apply_jobs_to_snapshots,
    load_notified_fingerprints,
)

DEFAULT_STATE_PATH = (
    Path(__file__).resolve().parent.parent / "data" / "saramin_notified.json"
)


def state_path() -> Path:
    custom = os.getenv("SARAMIN_STATE_FILE", "").strip()
    return Path(custom) if custom else DEFAULT_STATE_PATH


def deadline_marker(job: dict) -> str:
    date = str(job.get("date", "")).strip()
    if "내일마감" in date:
        return "내일마감"
    if "오늘마감" in date:
        return "오늘마감"
    return ""


def job_fingerprint(job: dict) -> str:
    """사람인은 제목 기준으로 중복을 막되, 내일/오늘마감 전환은 각각 1회 알림."""
    title = str(job.get("title", "")).strip()
    marker = deadline_marker(job)
    return f"{title}|{marker}" if marker else title


def _normalize_saramin_fp(fp: str) -> str:
    """이전 title|date 저장값은 title만 남기고, 마감 임박 marker는 유지."""
    if "|" not in fp:
        return fp
    title, marker = fp.rsplit("|", 1)
    if marker in {"내일마감", "오늘마감"}:
        return fp
    return title


def apply_jobs_to_snapshots(
    jobs: list[dict],
    snapshots: dict[str, str],
    notified: dict[str, list[str]],
    *,
    baseline: bool = False,
) -> tuple[list[tuple[dict, str]], dict[str, str], dict[str, list[str]]]:
    return _apply_jobs_to_snapshots(
        jobs,
        snapshots,
        notified,
        baseline=baseline,
        fingerprint_func=job_fingerprint,
        migrate_title_only_without_notify=False,
    )


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

    snapshots = data.get("job_snapshots", {})
    if not isinstance(snapshots, dict):
        snapshots = {}
    snapshots = {str(k): str(v) for k, v in snapshots.items() if k and v}
    return {
        "initialized": True,
        "job_snapshots": snapshots,
        "notified_fingerprints": load_notified_fingerprints(
            data,
            snapshots,
            normalize_func=_normalize_saramin_fp,
        ),
        "needs_baseline": bool(data.get("needs_baseline", False)),
    }


def save_state(state: dict) -> None:
    path = state_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    snapshots = state.get("job_snapshots", {})
    if not isinstance(snapshots, dict):
        snapshots = {}
    snapshots = {str(k): str(v) for k, v in snapshots.items() if k and v}

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
    }
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


__all__ = [
    "apply_jobs_to_snapshots",
    "job_fingerprint",
    "load_state",
    "save_state",
]
