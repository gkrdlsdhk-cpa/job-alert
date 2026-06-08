#!/usr/bin/env python3
"""딜로이트(안진회계법인) — 신입·Tax & Legal 검색 결과 실시간 카카오 알림."""

from __future__ import annotations

import sys
from pathlib import Path

import yaml
from dotenv import load_dotenv

from src.deloitte_careers import DEFAULT_HOME_URL, fetch_filtered_jobs
from src.deloitte_watch_state import (
    apply_jobs_to_snapshots,
    job_fingerprint,
    load_state,
    save_state,
)
from src.kakao_sender import send_deloitte_career_alert


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
        f"딜로이트 기준선 등록 ({reason}) — 화면에 있던 {len(snapshots)}건 "
        f"(ridx+제목+마감일) 저장. 이후 변경·신규만 카카오 알림."
    )
    return 0


def run_watch(*, seed_only: bool = False, dry_run: bool = False) -> int:
    config = load_config()
    watch_cfg = config.get("deloitte_watch", {})
    base_url = watch_cfg.get("home_url", DEFAULT_HOME_URL)
    exp_type = str(watch_cfg.get("exp_type", "1,3"))
    service = str(watch_cfg.get("service", "AB"))
    keyword = str(watch_cfg.get("keyword", ""))
    service_dtl = str(watch_cfg.get("service_dtl", ""))
    max_fetch = int(watch_cfg.get("max_results", 50))

    exp_label = watch_cfg.get("exp_type_label") or "신입"
    service_label = watch_cfg.get("service_label") or "Tax & Legal"
    print(
        f"딜로이트 채용 공고 확인 중 ({exp_label} / {service_label}, {base_url})..."
    )
    jobs = fetch_filtered_jobs(
        base_url,
        exp_type=exp_type,
        service=service,
        keyword=keyword,
        service_dtl=service_dtl,
        max_results=max_fetch,
    )
    jobs_with_id = [j for j in jobs if j.get("job_id")]

    for job in jobs_with_id:
        print(
            f"  [{job['company']}] {job['date']} | {job['title'][:55]} "
            f"(ridx={job['job_id']})"
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
        print("딜로이트: 변경·신규 공고 없음.")
        return 0

    print(f"딜로이트 알림 대상 {len(to_notify)}건:")
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
        send_deloitte_career_alert(title, job["link"])

    save_state(
        {
            "initialized": True,
            "job_snapshots": snapshots,
            "notified_fingerprints": notified,
            "needs_baseline": False,
        }
    )
    print(f"딜로이트 카카오톡 {len(to_notify)}건 발송 완료.")
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
