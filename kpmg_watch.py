#!/usr/bin/env python3
"""삼정 KPMG 채용 사이트 — 신입 공고 실시간 카카오 알림 (폴링)."""

from __future__ import annotations

import sys
from pathlib import Path

import yaml
from dotenv import load_dotenv

from src.kakao_sender import send_kpmg_career_alert
from src.kpmg_careers import DEFAULT_LIST_URL, fetch_new_graduate_jobs
from src.kpmg_watch_state import (
    apply_jobs_to_snapshots,
    job_fingerprint,
    load_state,
    save_state,
)


def load_config() -> dict:
    config_path = Path(__file__).parent / "config.yaml"
    with config_path.open(encoding="utf-8") as f:
        return yaml.safe_load(f)


def _baseline_current_jobs(jobs_with_id: list[dict], *, reason: str) -> int:
    state = load_state()
    _, snapshots, notified = apply_jobs_to_snapshots(
        jobs_with_id,
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
        f"삼정KPMG 기준선 등록 ({reason}) — 화면에 있던 {len(snapshots)}건 "
        f"(jobopen_id+제목+마감일) 저장. 이후 변경·신규만 카카오 알림."
    )
    return 0


def run_watch(*, seed_only: bool = False, dry_run: bool = False) -> int:
    config = load_config()
    watch_cfg = config.get("kpmg_watch", {})
    list_url = watch_cfg.get("list_url", DEFAULT_LIST_URL)
    receive_div_cd = str(watch_cfg.get("receive_div_cd", "N"))
    max_fetch = int(watch_cfg.get("max_results", 50))

    tab_label = {"N": "신입", "E": "경력", "O": "공채", "A": "전체"}.get(
        receive_div_cd, receive_div_cd
    )
    print(f"삼정KPMG 채용 공고 확인 중 ({tab_label} 탭, {list_url})...")
    jobs = fetch_new_graduate_jobs(
        list_url,
        receive_div_cd=receive_div_cd,
        max_results=max_fetch,
    )
    jobs_with_id = [j for j in jobs if j.get("job_id")]

    for job in jobs_with_id:
        print(
            f"  [{job['company']}] {job['date']} | {job['title'][:55]} "
            f"(jobopen_id={job['job_id']})"
        )

    state = load_state()
    snapshots = state.get("job_snapshots", {})
    notified = state.get("notified_fingerprints", {})

    if seed_only:
        return _baseline_current_jobs(jobs_with_id, reason="--seed")

    if state.get("needs_baseline"):
        return _baseline_current_jobs(
            jobs_with_id,
            reason="상태 파일 없음(캐시 미복구 — 이번 목록만 기준선)",
        )

    to_notify, snapshots, notified = apply_jobs_to_snapshots(
        jobs_with_id, snapshots, notified, baseline=False
    )

    if not to_notify:
        print("삼정KPMG: 변경·신규 공고 없음.")
        return 0

    print(f"삼정KPMG 알림 대상 {len(to_notify)}건:")
    for job, reason in to_notify:
        print(
            f"  - [{reason}] {job['company']} | {job['title'][:50]} | "
            f"{job['job_id']} | {job_fingerprint(job)}"
        )

    if dry_run:
        print("(dry-run) 카카오 발송 생략")
        save_state(
            {
                "initialized": True,
                "job_snapshots": snapshots,
                "notified_fingerprints": notified,
                "needs_baseline": False,
            }
        )
        return 0

    for job, reason in reversed(to_notify):
        title = job["title"]
        if reason == "수정·재게시":
            title = f"[재게시] {title}"
        send_kpmg_career_alert(title, job["link"])

    save_state(
        {
            "initialized": True,
            "job_snapshots": snapshots,
            "notified_fingerprints": notified,
            "needs_baseline": False,
        }
    )
    print(f"삼정KPMG 카카오톡 {len(to_notify)}건 발송 완료.")
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
