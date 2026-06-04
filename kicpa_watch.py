#!/usr/bin/env python3
"""회계사회 구인(수습CPA) 신규 공고 → 카카오톡 실시간 알림 (폴링)."""

from __future__ import annotations

import sys
from pathlib import Path

import yaml
from dotenv import load_dotenv

from src.kakao_sender import send_kicpa_job_alert
from src.kicpa_jobs import fetch_trainee_cpa_jobs
from src.kicpa_state import load_state, notified_id_set, save_state


def load_config() -> dict:
    config_path = Path(__file__).parent / "config.yaml"
    with config_path.open(encoding="utf-8") as f:
        return yaml.safe_load(f)


def _baseline_current_jobs(jobs_with_id: list[dict], *, reason: str) -> int:
    seen = {j["job_id"] for j in jobs_with_id if j.get("job_id")}
    save_state({"initialized": True, "notified_ids": sorted(seen), "needs_baseline": False})
    print(
        f"기준선 등록 ({reason}) — 화면에 있던 {len(seen)}건은 알림 없이 등록. "
        "이후 올라오는 공고만 카카오 알림."
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
    seen = notified_id_set(state)

    if seed_only:
        return _baseline_current_jobs(jobs_with_id, reason="--seed")

    if state.get("needs_baseline"):
        return _baseline_current_jobs(
            jobs_with_id,
            reason="상태 파일 없음(캐시 미복구 — 이번 목록만 기준선)",
        )

    new_jobs = [j for j in jobs_with_id if j["job_id"] not in seen]
    if not new_jobs:
        print("신규 공고 없음.")
        return 0

    print(f"신규 {len(new_jobs)}건 감지:")
    for job in new_jobs:
        print(f"  - {job['company']} | {job['title'][:50]} | {job['job_id']}")

    if dry_run:
        print("(dry-run) 카카오 발송 생략")
        return 0

    # 게시판은 최신이 위 → 오래된 순으로 알림 (읽기 순서 자연스럽게)
    for job in reversed(new_jobs):
        send_kicpa_job_alert(job["title"], job["link"])
        seen.add(job["job_id"])

    save_state({"initialized": True, "notified_ids": sorted(seen), "needs_baseline": False})
    print(f"신규 {len(new_jobs)}건 카카오톡 발송 완료.")
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
