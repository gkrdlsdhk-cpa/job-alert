#!/usr/bin/env python3
"""삼일PwC 정기채용 모집 오픈 → 카카오톡 알림 (폴링)."""

from __future__ import annotations

import sys
from pathlib import Path

import yaml
from dotenv import load_dotenv

from src.kakao_sender import send_pwc_recruitment_alert
from src.pwc_careers import check_graduate_recruitment
from src.pwc_state import load_state, save_state


def load_config() -> dict:
    config_path = Path(__file__).parent / "config.yaml"
    with config_path.open(encoding="utf-8") as f:
        return yaml.safe_load(f)


def run_watch(*, seed_only: bool = False) -> int:
    config = load_config()
    pwc_cfg = config.get("pwc", {})
    watch_url = pwc_cfg.get("watch_url", "https://pwc.to/2xLHIx4")

    print(f"삼일PwC 정기채용 확인 중 ({watch_url})...")
    status = check_graduate_recruitment(watch_url)

    if status.get("error"):
        print(f"경고: {status['summary']}")
        return 0

    state = load_state()
    fingerprint = status.get("fingerprint", "")
    is_open = bool(status.get("is_open"))

    print(
        f"상태: {'모집 중(오픈)' if is_open else '대기(미오픈)'} "
        f"| fingerprint={fingerprint}"
    )

    if seed_only or not state.get("initialized"):
        save_state(
            {
                "initialized": True,
                "notified_open": is_open,
                "last_open": is_open,
                "fingerprint": fingerprint,
            }
        )
        if is_open:
            print("초기화 — 현재 모집 중으로 보이지만 첫 등록만 했습니다 (알림 생략).")
        else:
            print("초기화 완료 — 모집 오픈 시 카카오 알림을 보냅니다.")
        return 0

    if not is_open:
        save_state(
            {
                "initialized": True,
                "notified_open": False,
                "last_open": False,
                "fingerprint": fingerprint,
            }
        )
        print("아직 모집이 열리지 않았습니다.")
        return 0

    already_notified = (
        state.get("notified_open")
        and state.get("fingerprint") == fingerprint
        and state.get("last_open")
    )
    if already_notified:
        print("이미 알림을 보낸 모집 상태입니다.")
        return 0

    title = status.get("title", "삼일PwC 정기채용 모집 시작")
    link = status.get("link", watch_url)

    save_state(
        {
            "initialized": True,
            "notified_open": True,
            "last_open": True,
            "fingerprint": fingerprint,
        }
    )
    send_pwc_recruitment_alert(title, link)
    print("모집 오픈 카카오톡 알림 발송 완료.")
    return 0


def main() -> int:
    load_dotenv()
    seed_only = "--seed" in sys.argv
    try:
        return run_watch(seed_only=seed_only)
    except Exception as exc:
        print(f"오류: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
