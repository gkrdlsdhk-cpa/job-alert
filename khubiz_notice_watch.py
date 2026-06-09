#!/usr/bin/env python3
"""경희대 경영대학 공지사항 — 채용 키워드 실시간 카카오 알림."""

from __future__ import annotations

import sys
from pathlib import Path

import yaml
from dotenv import load_dotenv

from src.kakao_sender import send_khubiz_notice_alert
from src.khubiz_notice_state import (
    apply_jobs_to_snapshots,
    job_fingerprint,
    load_state,
    save_state,
)
from src.khubiz_notices import DEFAULT_LIST_URL, fetch_notices, filter_notices_by_keywords


def load_config() -> dict:
    config_path = Path(__file__).parent / "config.yaml"
    with config_path.open(encoding="utf-8") as f:
        return yaml.safe_load(f)


def _baseline_current_notices(notices_with_id: list[dict], *, reason: str) -> int:
    state = load_state()
    _, snapshots, notified = apply_jobs_to_snapshots(
        notices_with_id,
        state.get("job_snapshots", {}),
        state.get("notified_fingerprints", {}),
        baseline=True,
    )
    save_state(
        {
            "initialized": True,
            "job_snapshots": snapshots,
            "notified_fingerprints": notified,
            "needs_baseline": False,
        }
    )
    print(
        f"경희대 경영대학 공지 기준선 등록 ({reason}) — "
        f"키워드 매칭 공지 {len(snapshots)}건 저장. 이후 신규만 카카오 알림."
    )
    return 0


def run_watch(*, seed_only: bool = False, dry_run: bool = False) -> int:
    config = load_config()
    watch_cfg = config.get("khubiz_notice_watch", {})
    list_url = watch_cfg.get("list_url", DEFAULT_LIST_URL)
    keywords = list(watch_cfg.get("keywords") or ["채용", "채용설명회"])
    max_fetch = int(watch_cfg.get("max_results", 20))

    print(f"경희대 경영대학 공지 확인 중 ({', '.join(keywords)})...")
    notices = fetch_notices(list_url, max_results=max_fetch)
    matched = filter_notices_by_keywords(notices, keywords)
    notices_with_id = [notice for notice in matched if notice.get("job_id")]

    for notice in notices_with_id:
        print(
            f"  [{notice.get('category', '')}] {notice.get('date', '')} | "
            f"{notice['title'][:60]} (boardId={notice['job_id']})"
        )

    state = load_state()
    snapshots = state.get("job_snapshots", {})
    notified = state.get("notified_fingerprints", {})

    if seed_only:
        return _baseline_current_notices(notices_with_id, reason="--seed")

    if state.get("needs_baseline"):
        return _baseline_current_notices(
            notices_with_id,
            reason="상태 파일 없음(상태 브랜치 미복구 — 이번 목록만 기준선)",
        )

    to_notify, snapshots, notified = apply_jobs_to_snapshots(
        notices_with_id, snapshots, notified, baseline=False
    )

    new_state = {
        "initialized": True,
        "job_snapshots": snapshots,
        "notified_fingerprints": notified,
        "needs_baseline": False,
    }

    if not to_notify:
        print("경희대 경영대학: 채용 키워드 신규 공지 없음.")
        save_state(new_state)
        return 0

    print(f"경희대 경영대학 알림 대상 {len(to_notify)}건:")
    for notice, reason in to_notify:
        print(
            f"  - [{reason}] {notice['title'][:50]} | "
            f"{notice['job_id']} | {job_fingerprint(notice)}"
        )

    save_state(new_state)

    if dry_run:
        print("(dry-run) 카카오 발송 생략")
        return 0

    for notice, _reason in reversed(to_notify):
        send_khubiz_notice_alert(notice["title"], notice["link"])

    print(f"경희대 경영대학 카카오톡 {len(to_notify)}건 발송 완료.")
    return 0


def main() -> int:
    load_dotenv()
    seed_only = "--seed" in sys.argv
    dry_run = "--dry-run" in sys.argv
    try:
        return run_watch(seed_only=seed_only, dry_run=dry_run)
    except Exception as exc:
        print(f"오류: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
