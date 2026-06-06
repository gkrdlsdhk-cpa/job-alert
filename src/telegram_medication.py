"""텔레그램 복약 알림 — 발송·버튼 응답 처리."""

from __future__ import annotations

import json
import os
import signal
import subprocess
import sys
import time
from pathlib import Path

import requests

from src.medication_state import (
    load_state,
    mark_morning_sent,
    mark_taken,
)
from src.telegram_sender import (
    CALLBACK_MED_TAKEN,
    answer_callback,
    get_updates,
    mark_message_taken,
    send_medication_reminder,
)

ROOT_DIR = Path(__file__).resolve().parent.parent
DEFAULT_POLL_STATE = ROOT_DIR / "data" / "telegram_poll_state.json"
WATCH_LOCK = ROOT_DIR / "data" / "telegram_watch.lock"


def _poll_state_path() -> Path:
    raw = os.getenv("TELEGRAM_POLL_STATE_FILE", "").strip()
    return Path(raw) if raw else DEFAULT_POLL_STATE


def _load_poll_offset() -> int | None:
    path = _poll_state_path()
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None
    offset = data.get("update_offset")
    return int(offset) if offset is not None else None


def _save_poll_offset(offset: int) -> None:
    path = _poll_state_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps({"update_offset": offset}, ensure_ascii=False),
        encoding="utf-8",
    )


def _flush_poll_queue() -> None:
    """이전 버튼 클릭 기록을 비워 새 알림과 섞이지 않게 함."""
    if _webhook_enabled():
        return
    offset = _load_poll_offset()
    updates = get_updates(offset=offset)
    if not updates:
        return
    max_update_id = max(u.get("update_id", 0) for u in updates)
    if offset is not None:
        max_update_id = max(max_update_id, offset)
    _save_poll_offset(max_update_id + 1)


def deliver_morning(message: str) -> None:
    state = load_state()
    if state.get("morning_sent"):
        print("복약(텔레그램): 오늘 아침 알림 이미 발송함 — 건너뜀.")
        return
    if state.get("taken"):
        print("복약(텔레그램): 오늘 이미 복용 체크됨 — 건너뜀.")
        return

    _flush_poll_queue()
    message_id = send_medication_reminder(message)
    state = mark_morning_sent()
    state["telegram_message_id"] = message_id
    state["telegram_message_ids"] = [message_id]
    from src.medication_state import save_state

    save_state(state)
    _spawn_watch_if_local()


def _process_updates(updates: list[dict], offset: int | None) -> int:
    handled = 0
    max_update_id = offset or 0

    for update in updates:
        update_id = update.get("update_id", 0)
        max_update_id = max(max_update_id, update_id)

        callback = update.get("callback_query")
        if not callback:
            continue
        if callback.get("data") != CALLBACK_MED_TAKEN:
            continue

        msg = callback.get("message") or {}
        chat_id = msg.get("chat", {}).get("id")
        message_id = msg.get("message_id")
        text = (msg.get("text") or "").replace("💊 ", "").replace("✅ ", "").strip()
        if "복용 완료" in text:
            continue

        state = load_state()
        already_taken_today = bool(state.get("taken"))

        if not already_taken_today:
            mark_taken()

        answer_callback(
            callback["id"],
            "오늘 이미 체크했어요." if already_taken_today else "복용 완료!",
        )

        if chat_id and message_id and text:
            try:
                mark_message_taken(chat_id, message_id, original_text=text)
            except requests.HTTPError:
                pass

        if message_id is not None:
            from src.medication_state import save_state

            ids = list(state.get("telegram_message_ids") or [])
            if int(message_id) not in ids:
                ids.append(int(message_id))
            state["telegram_message_ids"] = ids
            state["telegram_message_id"] = int(message_id)
            save_state(state)

        handled += 1
        print("복약(텔레그램): 복용 완료 버튼 처리됨.")

    if max_update_id:
        _save_poll_offset(max_update_id + 1)

    return handled


def poll_button_clicks() -> int:
    """인라인 버튼(복용 완료) 눌림 처리. 처리한 건수 반환."""
    if _webhook_enabled():
        print("복약(텔레그램): Webhook 모드 — poll 불필요.")
        return 0
    offset = _load_poll_offset()
    updates = get_updates(offset=offset)
    if not updates:
        return 0
    return _process_updates(updates, offset)


def _watch_lock_pid() -> int | None:
    if not WATCH_LOCK.exists():
        return None
    try:
        pid = int(WATCH_LOCK.read_text(encoding="utf-8").strip())
        os.kill(pid, 0)
        return pid
    except (OSError, ValueError):
        WATCH_LOCK.unlink(missing_ok=True)
        return None


def _stop_watch() -> None:
    pid = _watch_lock_pid()
    if pid is None:
        return
    try:
        os.kill(pid, signal.SIGTERM)
    except OSError:
        pass
    WATCH_LOCK.unlink(missing_ok=True)


def _webhook_enabled() -> bool:
    return os.getenv("TELEGRAM_USE_WEBHOOK", "").strip() == "1"


def _spawn_watch_if_local() -> None:
    """맥 로컬: 알림 후 백그라운드에서 버튼 클릭을 자동 감시."""
    if _webhook_enabled():
        print("복약(텔레그램): Webhook 모드 — 버튼은 Worker가 즉시 처리합니다.")
        return
    if os.getenv("GITHUB_ACTIONS") or os.getenv("CI"):
        return
    if os.getenv("TELEGRAM_WATCH", "1").strip() == "0":
        return
    _stop_watch()

    script = ROOT_DIR / "telegram_watch.py"
    subprocess.Popen(
        [sys.executable, str(script), "--max-minutes", "180"],
        cwd=ROOT_DIR,
        start_new_session=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    print("복약(텔레그램): 버튼 감시 시작 — 누르면 곧바로 반영됩니다.")


def watch_button_clicks(
    *,
    max_minutes: int = 180,
    exit_when_taken: bool = False,
) -> None:
    """Long polling으로 버튼 클릭을 실시간 감시."""
    if _webhook_enabled():
        print("복약(텔레그램): Webhook 모드 — watch 불필요.")
        return
    if os.getenv("GITHUB_ACTIONS") or os.getenv("CI"):
        exit_when_taken = True

    WATCH_LOCK.parent.mkdir(parents=True, exist_ok=True)
    WATCH_LOCK.write_text(str(os.getpid()), encoding="utf-8")
    deadline = time.monotonic() + max_minutes * 60

    try:
        while time.monotonic() < deadline:
            if exit_when_taken and load_state().get("taken"):
                print("복약(텔레그램): 복용 체크 완료 — 감시 종료.")
                return

            offset = _load_poll_offset()
            updates = get_updates(offset=offset, timeout=25)
            if updates:
                _process_updates(updates, offset)
    finally:
        WATCH_LOCK.unlink(missing_ok=True)
