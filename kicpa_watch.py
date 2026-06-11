#!/usr/bin/env python3
"""회계사회 구인(CPA/수습CPA) 신규·수정 공고 → 카카오톡 실시간 알림 (폴링)."""

from __future__ import annotations

import sys
from pathlib import Path

import yaml
from dotenv import load_dotenv

from src.kakao_sender import send_kicpa_job_alert
from src.kicpa_jobs import fetch_cpa_jobs, fetch_trainee_cpa_jobs
from src.kicpa_state import apply_jobs_to_snapshots, job_fingerprint, load_state, save_state
from src.realtime_job_filters import filter_jobs_by_excluded_titles, global_excluded_title_keywords


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
    board_baselines = dict(state.get("board_baselines", {}))
    for job in jobs_with_id:
        board = str(job.get("board", "")).strip()
        if board:
            board_baselines[board] = True
    save_state(
        {
            "initialized": True,
            "job_snapshots": snapshots,
            "notified_fingerprints": notified,
            "needs_baseline": False,
            "board_baselines": board_baselines,
        }
    )
    print(
        f"기준선 등록 ({reason}) — 화면에 있던 {len(snapshots)}건 "
        f"(job_id+제목+등록일) 저장. 이후 변경·신규만 카카오 알림."
    )
    return 0


def run_watch(*, seed_only: bool = False, dry_run: bool = False) -> int:
    config = load_config()
    kicpa_cfg = config.get("kicpa", {})
    list_size = int(kicpa_cfg.get("watch_list_size", 30))

    print(f"회계사회 구인(CPA/수습CPA) 확인 중 (최근 {list_size}건씩)...")
    trainee_jobs = fetch_trainee_cpa_jobs(list_size)
    cpa_jobs = fetch_cpa_jobs(list_size)
    print(f"  구인(수습CPA): {len(trainee_jobs)}건")
    print(f"  구인(CPA): {len(cpa_jobs)}건")
    jobs = trainee_jobs + cpa_jobs
    jobs_with_id = [j for j in jobs if j.get("job_id")]
    jobs_with_id, skipped_jobs = filter_jobs_by_excluded_titles(
        jobs_with_id,
        global_excluded_title_keywords(config),
    )
    for job in skipped_jobs:
        print(f"  제외(제목 필터): {job['title'][:55]} (job_id={job['job_id']})")

    state = load_state()
    snapshots = state.get("job_snapshots", {})
    notified = state.get("notified_fingerprints", {})
    board_baselines = state.get("board_baselines", {})

    if seed_only:
        result = _baseline_current_jobs(jobs_with_id, reason="--seed")
        state = load_state()
        board_baselines = state.get("board_baselines", {})
        board_baselines["구인(CPA)"] = True
        board_baselines["구인(수습CPA)"] = True
        state["board_baselines"] = board_baselines
        save_state(state)
        return result

    if state.get("needs_baseline"):
        return _baseline_current_jobs(
            jobs_with_id,
            reason="상태 파일 없음(캐시 미복구 — 이번 목록만 기준선)",
        )

    cpa_board_jobs = [job for job in jobs_with_id if job.get("board") == "구인(CPA)"]
    if cpa_board_jobs and not board_baselines.get("구인(CPA)"):
        _, snapshots, notified = apply_jobs_to_snapshots(
            cpa_board_jobs, snapshots, notified, baseline=True
        )
        board_baselines["구인(CPA)"] = True
        print(
            f"회계사회 구인(CPA) 기준선 등록 — 현재 {len(cpa_board_jobs)}건 저장. "
            "이후 변경·신규만 카카오 알림."
        )

    to_notify, snapshots, notified = apply_jobs_to_snapshots(
        jobs_with_id, snapshots, notified, baseline=False
    )

    new_state = {
        "initialized": True,
        "job_snapshots": snapshots,
        "notified_fingerprints": notified,
        "needs_baseline": False,
        "board_baselines": board_baselines,
    }

    if not to_notify:
        print("변경·신규 공고 없음.")
        save_state(new_state)
        return 0

    print(f"알림 대상 {len(to_notify)}건:")
    for job, reason in to_notify:
        print(
            f"  - [{reason}] {job.get('board', '회계사회')} | {job['company']} | {job['title'][:50]} | "
            f"{job['job_id']} | {job_fingerprint(job)}"
        )

    save_state(new_state)

    if dry_run:
        print("(dry-run) 카카오 발송 생략")
        return 0

    for job, reason in reversed(to_notify):
        label = job.get("alert_label", "수습CPA")
        prefix_title = job["title"]
        if reason == "수정·재게시":
            prefix_title = f"[재게시] {prefix_title}"
        send_kicpa_job_alert(prefix_title, job["link"], label=label)

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
