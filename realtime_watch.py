#!/usr/bin/env python3
"""Realtime Job Alerts 오케스트레이터 — step 실패 시에도 다음 watch 계속 실행."""

from __future__ import annotations

import sys
import traceback
from collections.abc import Callable
from dataclasses import dataclass

from dotenv import load_dotenv

import deloitte_watch
import ey_watch
import khubiz_notice_watch
import kicpa_watch
import kpmg_watch
import pwc_watch
import saramin_watch
from src.kakao_sender import send_realtime_watch_failure_alert


@dataclass(frozen=True)
class WatchStep:
    label: str
    run: Callable[..., int]
    pass_dry_run: bool = True


def _run_pwc(*, seed_only: bool = False, dry_run: bool = False) -> int:
    return pwc_watch.run_watch(seed_only=seed_only)


WATCH_STEPS: list[WatchStep] = [
    WatchStep("회계사회", kicpa_watch.run_watch),
    WatchStep("삼일PwC", _run_pwc, pass_dry_run=False),
    WatchStep("사람인 Big4", saramin_watch.run_watch),
    WatchStep("삼정KPMG", kpmg_watch.run_watch),
    WatchStep("EY한영", ey_watch.run_watch),
    WatchStep("딜로이트", deloitte_watch.run_watch),
    WatchStep("경희대 경영대학", khubiz_notice_watch.run_watch),
]


def run_all(*, seed_only: bool = False, dry_run: bool = False) -> int:
    failures: list[tuple[int, str, str]] = []
    total_steps = len(WATCH_STEPS)

    for step_no, step in enumerate(WATCH_STEPS, start=1):
        print(f"\n=== [{step_no}/{total_steps}] {step.label} ===")
        try:
            kwargs: dict = {"seed_only": seed_only}
            if step.pass_dry_run:
                kwargs["dry_run"] = dry_run
            code = step.run(**kwargs)
            if code != 0:
                failures.append((step_no, step.label, f"종료 코드 {code}"))
        except Exception as exc:
            print(f"오류 ({step.label}): {exc}", file=sys.stderr)
            traceback.print_exc()
            failures.append((step_no, step.label, str(exc) or exc.__class__.__name__))
        print(f"=== [{step_no}/{total_steps}] {step.label} 완료 ===")

    if not failures:
        return 0

    failed_labels = ", ".join(f"{no}.{label}" for no, label, _ in failures)
    print(f"실패 {len(failures)}건: {failed_labels}")
    if not dry_run:
        try:
            send_realtime_watch_failure_alert(failures, total_steps=total_steps)
        except Exception as exc:
            print(f"실패 알림 발송 오류: {exc}", file=sys.stderr)
    return 1


def main() -> int:
    load_dotenv()
    seed_only = "--seed" in sys.argv
    dry_run = "--dry-run" in sys.argv
    return run_all(seed_only=seed_only, dry_run=dry_run)


if __name__ == "__main__":
    raise SystemExit(main())
