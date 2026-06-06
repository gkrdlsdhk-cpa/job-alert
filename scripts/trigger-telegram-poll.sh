#!/usr/bin/env bash
# Telegram Medication Poll 워크플로 트리거

set -euo pipefail

OWNER="${GITHUB_OWNER:-gkrdlsdhk-cpa}"
REPO="${GITHUB_REPO:-job-alert}"
WORKFLOW="${GITHUB_WORKFLOW:-telegram-poll.yml}"
REF="${GITHUB_REF:-main}"

if [[ -z "${GITHUB_TOKEN:-}" ]]; then
  echo "GITHUB_TOKEN 환경 변수를 설정하세요." >&2
  exit 1
fi

url="https://api.github.com/repos/${OWNER}/${REPO}/actions/workflows/${WORKFLOW}/dispatches"

http_code="$(
  curl -sS -o /tmp/trigger-telegram-poll.json -w "%{http_code}" \
    -X POST "$url" \
    -H "Accept: application/vnd.github+json" \
    -H "Authorization: Bearer ${GITHUB_TOKEN}" \
    -H "X-GitHub-Api-Version: 2022-11-28" \
    -H "Content-Type: application/json" \
    -d "{\"ref\":\"${REF}\"}"
)"

if [[ "$http_code" == "204" ]]; then
  echo "OK — Telegram Poll 트리거됨"
  exit 0
fi

echo "실패 (HTTP ${http_code}):" >&2
cat /tmp/trigger-telegram-poll.json >&2
exit 1
