#!/usr/bin/env python3
"""회계사회 구인(수습CPA) 신규·수정 공고 → 카카오톡 실시간 알림 (폴링)."""

from __future__ import annotations

import sys
from pathlib import Path

import yaml
from dotenv import load_dotenv

from src.kakao_sender import send_kicpa_job_alert
from src.kicpa_jobs import fetch_trainee_cpa_jobs
from src.kicpa_state import apply_jobs_to_snapshots, job_fingerprint, load_state, save_state


def load_config() -> dict:
    config_path = Path(__file__).parent / "config.yaml"
    with config_path.open(encoding="utf-8") as f:
        return yaml.safe_load(f)


def _baseline_current_jobs(jobs_with_id: list[dict], *, reason: str) -> int:
    state = load_state()
    _, snapshots = apply_jobs_to_snapshots(
        jobs_with_id, state.get("job_snapshots", {}), baseline=True
    )
    save_state({"initialized": True, "job_snapshots": snapshots, "needs_baseline": False})
    print(
        f"기준선 등록 ({reason}) — 화면에 있던 {len(snapshots)}건 "
        f"(job_id+제목+등록일) 저장. 이후 변경·신규만 카카오 알림."
    )
    return 0


def run_watch(*, seed_only: bool = False, dry_run: bool = False) -> int:
    config = load_config()
    kicpa_cfg = config.get("kicpa", {})
    list_size = int(kicpa_cfg.get("watch_list_size", 30))

    print(f"회계사회 구인(수습CPA) 확인 중 (최근 {list_size}건)...")
    jobs = fetch_trainee_cpa_jobs(list_size)
    jobs_with_id = [j for j in jobs if j.get("job_id")]

    state = load_state()
    snapshots = state.get("job_snapshots", {})

    if seed_only:
        return _baseline_current_jobs(jobs_with_id, reason="--seed")

    if state.get("needs_baseline"):
        return _baseline_current_jobs(
            jobs_with_id,
            reason="상태 파일 없음(캐시 미복구 — 이번 목록만 기준선)",
        )

    to_notify, snapshots = apply_jobs_to_snapshots(jobs_with_id, snapshots, baseline=False)

    if not to_notify:
        print("변경·신규 공고 없음.")
        return 0

    print(f"알림 대상 {len(to_notify)}건:")
    for job, reason in to_notify:
        print(
            f"  - [{reason}] {job['company']} | {job['title'][:50]} | "
            f"{job['job_id']} | {job_fingerprint(job)}"
        )

    if dry_run:
        print("(dry-run) 카카오 발송 생략")
        save_state({"initialized": True, "job_snapshots": snapshots, "needs_baseline": False})
        return 0

    for job, reason in reversed(to_notify):
        prefix_title = job["title"]
        if reason == "수정·재게시":
            prefix_title = f"[재게시] {prefix_title}"
        send_kicpa_job_alert(prefix_title, job["link"])

    save_state({"initialized": True, "job_snapshots": snapshots, "needs_baseline": False})
    print(f"카카오톡 {len(to_notify)}건 발송 완료.")
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
