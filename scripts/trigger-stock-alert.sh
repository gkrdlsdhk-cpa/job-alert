#!/usr/bin/env bash
# Morning Stock Alert 워크플로를 API로 트리거 (cron-job.org 테스트용)
# 사용: GITHUB_TOKEN=github_pat_xxx ./scripts/trigger-stock-alert.sh

set -euo pipefail

OWNER="${GITHUB_OWNER:-gkrdlsdhk-cpa}"
REPO="${GITHUB_REPO:-job-alert}"
WORKFLOW="${GITHUB_WORKFLOW:-stock-alert.yml}"
REF="${GITHUB_REF:-main}"

if [[ -z "${GITHUB_TOKEN:-}" ]]; then
  echo "GITHUB_TOKEN 환경 변수를 설정하세요. (Fine-grained PAT, Actions: Read and write)" >&2
  exit 1
fi

url="https://api.github.com/repos/${OWNER}/${REPO}/actions/workflows/${WORKFLOW}/dispatches"

http_code="$(
  curl -sS -o /tmp/trigger-stock-alert.json -w "%{http_code}" \
    -X POST "$url" \
    -H "Accept: application/vnd.github+json" \
    -H "Authorization: Bearer ${GITHUB_TOKEN}" \
    -H "X-GitHub-Api-Version: 2022-11-28" \
    -H "Content-Type: application/json" \
    -d "{\"ref\":\"${REF}\"}"
)"

if [[ "$http_code" == "204" ]]; then
  echo "OK — Morning Stock Alert 트리거됨 (ref=${REF})"
  echo "GitHub → Actions 에서 실행 여부를 확인하세요."
  exit 0
fi

echo "실패 (HTTP ${http_code}):" >&2
cat /tmp/trigger-stock-alert.json >&2
exit 1
