#!/usr/bin/env python3
"""매일 복약 알림 (텔레그램)."""

from __future__ import annotations

import sys
from pathlib import Path

import yaml
from dotenv import load_dotenv

from src.telegram_medication import deliver_morning


def load_config() -> dict:
    config_path = Path(__file__).parent / "config.yaml"
    with config_path.open(encoding="utf-8") as f:
        return yaml.safe_load(f)


def deliver_medication_alert() -> None:
    config = load_config()
    med_cfg = config.get("medication_alert", {})
    message = (med_cfg.get("message") or "아침 약 드실 시간이에요.").strip()
    deliver_morning(message)


def main() -> int:
    load_dotenv()
    try:
        deliver_medication_alert()
        return 0
    except Exception as exc:
        print(f"오류: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
