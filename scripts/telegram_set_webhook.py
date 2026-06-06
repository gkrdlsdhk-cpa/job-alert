#!/usr/bin/env python3
"""텔레그램 Webhook 등록/해제.

Webhook 사용 시 getUpdates(로컬 watch)는 동작하지 않습니다.
로컬에서 버튼 테스트할 때만 --delete 로 해제하세요.
"""

from __future__ import annotations

import argparse
import os
import re
import sys

import requests
from dotenv import load_dotenv

_SECRET_RE = re.compile(r"^[A-Za-z0-9_-]{1,256}$")


def _api(token: str, method: str, **payload: object) -> dict:
    response = requests.post(
        f"https://api.telegram.org/bot{token}/{method}",
        json=payload,
        timeout=15,
    )
    data = response.json()
    if not response.ok or not data.get("ok"):
        desc = data.get("description", response.text)
        raise RuntimeError(f"Telegram API 오류: {desc}")
    return data


def main() -> int:
    parser = argparse.ArgumentParser(description="텔레그램 Webhook 등록/해제")
    parser.add_argument(
        "--delete",
        action="store_true",
        help="Webhook 해제 (로컬 watch 테스트용)",
    )
    parser.add_argument(
        "--info",
        action="store_true",
        help="현재 Webhook 상태만 출력",
    )
    args = parser.parse_args()

    load_dotenv()
    token = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
    if not token:
        print("TELEGRAM_BOT_TOKEN을 .env에 설정하세요.", file=sys.stderr)
        return 1

    if args.info or args.delete:
        info = _api(token, "getWebhookInfo")
        print(info.get("result", {}))
        if args.info:
            return 0

    if args.delete:
        result = _api(token, "deleteWebhook", drop_pending_updates=True)
        print("Webhook 해제됨:", result.get("result"))
        return 0

    webhook_url = os.getenv("TELEGRAM_WEBHOOK_URL", "").strip().rstrip("/")
    if not webhook_url:
        print(
            "TELEGRAM_WEBHOOK_URL을 .env에 설정하세요.\n"
            "예: https://job-alert-telegram-webhook.your-subdomain.workers.dev",
            file=sys.stderr,
        )
        return 1

    secret = os.getenv("TELEGRAM_WEBHOOK_SECRET", "").strip()
    if secret and not _SECRET_RE.fullmatch(secret):
        print(
            "TELEGRAM_WEBHOOK_SECRET은 영문·숫자·_·- 만 가능합니다. (! @ 등 특수문자 불가)",
            file=sys.stderr,
        )
        return 1

    payload: dict = {
        "url": webhook_url,
        "allowed_updates": ["callback_query"],
        "drop_pending_updates": True,
    }
    if secret:
        payload["secret_token"] = secret

    result = _api(token, "setWebhook", **payload)
    print("Webhook 등록됨:", result.get("result"))
    print(f"URL: {webhook_url}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
