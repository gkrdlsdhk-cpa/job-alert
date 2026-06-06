# 클라oud로 매일 12시 자동 발송 (GitHub Actions)

Mac이 꺼져 있어도 **cron-job.org**가 매일 **한국 시간 12:00**에 GitHub Actions로 `main.py`를 실행합니다.

---

## 1. GitHub 저장소 만들기

1. [github.com](https://github.com) 로그인
2. 우측 상단 **+** → **New repository**
3. Repository name: `job-alert` (아무 이름이나 OK)
4. **Private** 선택 (API 키·토큰 코드가 올라가므로 **공개 저장소 금지**)
5. **Create repository**

---

## 2. 코드 올리기 (터미널)

GitHub에서 만든 저장소 주소를 본인 것으로 바꿔서 실행하세요.

```bash
cd ~/job-alert
git init
git add .
git commit -m "Add job-alert with GitHub Actions daily schedule"
git branch -M main
git remote add origin https://github.com/gkrdlsdhk-cpa/job-alert.git
git push -u origin main
```

> 이미 올려 두었다면 2번은 건너뛰고 **3번 Secrets**부터 하면 됩니다.  
> 저장소: https://github.com/gkrdlsdhk-cpa/job-alert

> `git` 명령이 안 되면: `xcode-select --install` 먼저 실행

---

## 3. GitHub Secrets 등록

GitHub 저장소 → **Settings** → **Secrets and variables** → **Actions** → **New repository secret**

`.env` 파일에 있는 값을 **하나씩** Secret으로 등록합니다.

| Secret 이름 | 필수 | 설명 |
|-------------|------|------|
| `NAVER_CLIENT_ID` | ✅ | 네이버 Client ID |
| `NAVER_CLIENT_SECRET` | ✅ | 네이버 Client Secret |
| `NOTIFY_VIA` | ✅ | `both` 추천 (Gmail 전체 + 카카오 알림) / `email` / `kakao` |
| `EMAIL_FROM` | ✅ | Gmail 주소 |
| `EMAIL_PASSWORD` | ✅ | Gmail 앱 비밀번호 |
| `EMAIL_TO` | ✅ | 받을 Gmail (본인 주소) |
| `KAKAO_REST_API_KEY` | 카카오 알림 시 | REST API 키 |
| `KAKAO_REFRESH_TOKEN` | 카카오 알림 시 | refresh token |
| `KAKAO_CLIENT_SECRET` | 선택 | Client Secret **사용** 중일 때만 |

> **`.env` 파일 자체는 GitHub에 올리지 마세요.** Secret으로만 등록합니다.

---

## 4. 수동 테스트

### 매일 12시 브리핑 (뉴스 + 사람인)

GitHub → **Actions** → **Daily Job Briefing** → **Run workflow**

1~2분 후:
- **Gmail** `[취업 브리핑]` 메일 (뉴스 + 사람인)
- **카카오톡** 「Gmail 확인」 알림 (`NOTIFY_VIA=both` 또는 `kakao`일 때)

- **매일 12:00 KST** 자동 실행 → **§8 cron-job.org** 권장

### 매일 9시 미국 주식 시세 (나스닥·테슬라·엔비디아)

GitHub → **Actions** → **Morning Stock Alert** → **Run workflow**

1~2분 후 카카오톡 **나와의 채팅**에 `<주가보고>` 메시지 (가격 + 전일 대비 %).

- 필요 Secret: `KAKAO_REST_API_KEY`, `KAKAO_REFRESH_TOKEN`
- 카카오 **제품 링크 관리** 웹 도메인: `https://m.stock.naver.com`
- **매일 09:00 KST** 자동 실행 → **§7 cron-job.org** 권장 (GitHub 내장 9시 cron은 자주 스킵됨)

### 실시간 카카오 알림 (회계사회 + 삼일PwC 정기채용)

GitHub → **Actions** → **Realtime Job Alerts** → **Run workflow**

| 대상 | 알림 시점 | 카카오 메시지 |
|------|-----------|----------------|
| 회계사회 구인(수습CPA) | 신규 공고 또는 **같은 ID에 제목·등록일 변경(재게시)** | `[회계사회 수습CPA 신규]` / `[재게시]…` + 공고 보기 |
| 삼일PwC 정기채용 | 모집 오픈(지원 링크·모집 중 문구 등장) | `[삼일PwC 정기채용]` + 채용 보기 |

- **첫 실행(또는 캐시 없음)**: 그때 목록에 있던 공고만 등록 (알림 없음). **그 직후 올라온 글부터** 알림
- 놓친 공고가 있으면 Actions 로그에 `기준선 등록` / `신규 N건` 확인
- **이후 ~10분마다** 자동 확인 → **§6 외부 스케줄러** 권장 (GitHub 내장 10분 cron은 자주 스킵됨)
- 필요 Secret: `KAKAO_REST_API_KEY`, `KAKAO_REFRESH_TOKEN`
- 카카오 **제품 링크 관리** 웹 도메인: `https://www.kicpa.or.kr`, `https://www.pwc.com`

---

## 6. 실시간 알림 — 외부 스케줄러 10분 (Mac 없을 때, 권장)

GitHub Actions의 `*/10` cron은 **하루에 몇 번만** 돌아가는 경우가 많습니다.  
**cron-job.org** 같은 외부 서비스가 **10분마다** `workflow_dispatch` API를 호출하면 Mac 없이도 비교적 규칙적으로 확인합니다.

### 6-1. GitHub 토큰 만들기

1. GitHub → **Settings** → **Developer settings** → **Fine-grained personal access tokens** → **Generate new token**
2. **Repository access**: `job-alert`만 선택
3. **Permissions** → **Actions**: **Read and write**
4. 생성된 토큰(`github_pat_...`)을 복사 — **cron-job.org에만** 넣고 코드·저장소에 올리지 마세요.

> Private 저장소면 Classic PAT(`repo` 권한)도 가능하지만, Fine-grained가 더 안전합니다.

### 6-2. 로컬에서 한 번 테스트 (선택)

```bash
chmod +x ~/job-alert/scripts/trigger-realtime-watch.sh
GITHUB_TOKEN=github_pat_여기에_붙여넣기 ~/job-alert/scripts/trigger-realtime-watch.sh
```

1~2분 후 **Actions → Realtime Job Alerts**에 **workflow_dispatch** 실행이 생기면 성공입니다.

### 6-3. cron-job.org 설정

1. [cron-job.org](https://cron-job.org) 가입·로그인
2. **Cronjobs** → **Create cronjob**
3. 아래처럼 입력:

| 항목 | 값 |
|------|-----|
| **Title** | job-alert realtime |
| **URL** | `https://api.github.com/repos/gkrdlsdhk-cpa/job-alert/actions/workflows/kicpa-watch.yml/dispatches` |
| **Schedule** | 평일만: cron `*/10 * * * 1-5` / 주말 포함: `*/10 * * * *` |
| **Request method** | **POST** |
| **Headers** | `Accept: application/vnd.github+json` |
| | `Authorization: Bearer github_pat_여기에_토큰` |
| | `X-GitHub-Api-Version: 2022-11-28` |
| **Request body** | `{"ref":"main"}` |
| **Content-Type** | `application/json` (본문 JSON일 때) |

4. **Enable** 저장

### 6-4. 동작 확인

- **10~15분** 후 Actions에 **workflow_dispatch**가 **10분 간격**으로 쌓이는지 확인
- 공고가 없으면 실행만 되고 **카톡은 안 옴** (정상)
- 워크플로에는 **매시 1회 백업 cron**만 남아 있음 — 외부 스케줄러가 멈춰도 최대 1시간마다 한 번은 확인

### 6-5. 주의

- 토큰 유출 시 GitHub에서 **즉시 폐기** 후 cron-job.org 헤더 갱신
- 무료 플랜으로도 10분 주기 가능 (cron-job.org 기준)
- 월 Actions 사용량: 10분마다 ≈ 하루 144회 × ~20초 — 개인 private 저장소 무료 한도 안이면 충분

---

## 7. 주가보고 9시 — cron-job.org (권장)

GitHub Actions `schedule`만으로는 **9시에 안 오는** 경우가 많습니다.  
**cron-job.org**에서 **매일 09:00 (KST)** 에 `Morning Stock Alert`를 호출하면 정시에 가깝게 동작합니다.

> 실시간 알림(§6)과 **같은 PAT**를 쓸 수 있습니다. cron-job **잡을 하나 더** 만드세요.

### 7-1. 로컬 테스트 (선택)

```bash
chmod +x ~/job-alert/scripts/trigger-stock-alert.sh
GITHUB_TOKEN=github_pat_여기에_붙여넣기 ~/job-alert/scripts/trigger-stock-alert.sh
```

### 7-2. cron-job.org — 두 번째 cronjob

1. **Cronjobs** → **Create cronjob**
2. 아래처럼 입력 (§6과 동일한 **ADVANCED** 설정: POST, 헤더, body)

| 항목 | 값 |
|------|-----|
| **Title** | `job alert stock 9am` |
| **URL** | `https://api.github.com/repos/gkrdlsdhk-cpa/job-alert/actions/workflows/stock-alert.yml/dispatches` |
| **Schedule** | Custom crontab: `0 9 * * *` |
| **Time zone** | `Asia/Seoul` |
| **Request method** | **POST** |
| **Headers** | §6과 동일 (`Accept`, `Authorization`, `X-GitHub-Api-Version`, `Content-Type`) |
| **Request body** | `{"ref":"main"}` |

3. **SAVE** → **TEST RUN** → `204` 확인

### 7-3. 하루 1회·백업

- `stock_alert.py`가 `stock_daily_sent.json`으로 **당일 중복 카톡** 방지 (TEST RUN·수동 실행도 스킵)
- 평일 9시대 **Realtime Job Alerts**가 돌면 `stock_daily_guard`가 **아직 안 보냈을 때만** 1회 백업 시도

### 7-4. 주말

- 주가 알림은 **매일 9시** (`0 9 * * *`) — 주말에도 전일 종가 기준으로 보냄
- 실시간 공고(§6)만 평일(`1-5`)로 끄면 됨

---

## 8. 취업 브리핑 12시 — cron-job.org (권장)

GitHub 내장 12시 cron은 **몇 시간 늦게** 돌 수 있습니다.  
**cron-job.org**에서 **매일 12:00 (KST)** 에 `Daily Job Briefing`을 호출하세요.

> **같은 PAT** 사용. cron-job **잡을 하나 더** 만듭니다 (총 3개: 실시간·주가·브리핑).

### 8-1. 로컬 테스트 (선택)

```bash
chmod +x ~/job-alert/scripts/trigger-daily-briefing.sh
GITHUB_TOKEN=github_pat_여기에_붙여넣기 ~/job-alert/scripts/trigger-daily-briefing.sh
```

### 8-2. cron-job.org — 세 번째 cronjob

| 항목 | 값 |
|------|-----|
| **Title** | `job alert briefing 12pm` |
| **URL** | `https://api.github.com/repos/gkrdlsdhk-cpa/job-alert/actions/workflows/daily-briefing.yml/dispatches` |
| **Schedule** | Custom crontab: `0 12 * * *` |
| **Time zone** | `Asia/Seoul` |
| **Request method** | **POST** |
| **Headers** | §6과 동일 |
| **Request body** | `{"ref":"main"}` |

**SAVE** → **TEST RUN** → `204` → Actions에 **Daily Job Briefing** 1회 확인.

### 8-3. cron-job 요약 (아래 §9 복약 포함)

| Title | Schedule (KST) | 워크플로 |
|-------|----------------|----------|
| job alert realtime | `*/10 9-18 * * 1-5` (평일 9~19시 10분) | `kicpa-watch.yml` |
| job alert stock 9am | `0 9 * * *` (매일 9시) | `stock-alert.yml` |
| job alert briefing 12pm | `0 12 * * *` (매일 12시) | `daily-briefing.yml` |
| job alert medication 9am | `0 9 * * *` (매일 9시) | `medication-alert.yml` |
| job alert medication 11am | `0 11 * * *` (매일 11시) | `medication-followup.yml` |

브리핑 **카톡만 끄려면** GitHub Secret `NOTIFY_VIA` → `email`.

---

## 9. 복약 알림 9시 + 복용 완료 버튼

매일 **09:00** 카카오 알림 → **「복용 완료 ✅」** 버튼 → 체크 시 “오늘 복용함” 기록.  
**11:00**까지 체크 없으면 **1회** 재알림.

### 9-1. Google Apps Script (버튼 → 체크 기록)

1. [script.google.com](https://script.google.com) → 새 프로젝트
2. `scripts/medication-mark-gas.gs` 내용 붙여넣기
3. **프로젝트 설정 → 스크립트 속성** 추가:

| 속성 | 값 |
|------|-----|
| `MARK_SECRET` | 임의 비밀 문자열 (예: `my-med-secret-42`) |
| `GITHUB_PAT` | job-alert용 `github_pat_...` (Actions Read and write) |
| `GITHUB_REPO` | `gkrdlsdhk-cpa/job-alert` |

4. **배포 → 새 배포 → 웹 앱** (실행: 나, 액세스: **모든 사용자**)
5. 배포 URL 예: `https://script.google.com/macros/s/XXXX/exec`
6. GitHub → **Secrets** → `MEDICATION_MARK_SECRET` = 위 `MARK_SECRET` 과 **동일**
7. `config.yaml` → `medication_alert.mark_taken_url`:

```yaml
mark_taken_url: "https://script.google.com/macros/s/XXXX/exec?key=my-med-secret-42"
```

8. push 후 카카오 **제품 링크 관리** 웹 도메인: `https://script.google.com`

### 9-2. cron-job.org — 복약 cronjob 2개

**아침 알림 (9시)**

| 항목 | 값 |
|------|-----|
| **Title** | `job alert medication 9am` |
| **URL** | `.../medication-alert.yml/dispatches` |
| **Schedule** | `0 9 * * *` / `Asia/Seoul` |
| **ADVANCED** | §6과 동일 |

**후속 알림 (11시, 체크 없을 때만)**

| 항목 | 값 |
|------|-----|
| **Title** | `job alert medication 11am` |
| **URL** | `.../medication-followup.yml/dispatches` |
| **Schedule** | `0 11 * * *` / `Asia/Seoul` |
| **ADVANCED** | §6과 동일 |

### 9-3. 동작 확인

1. **9시** 카카오 → **복용 완료 ✅** 버튼
2. 버튼 탭 → 브라우저 **「✅ 복용 완료」** → Actions **Medication Mark Taken** 실행
3. **11시** 전에 체크했으면 후속 알림 **안 옴** / 안 했으면 **재알림 1통**

### 9-4. 메시지 변경 (선택)

`config.yaml` → `medication_alert.message`, `follow_up_message`

> **텔레그램 사용 시** → 아래 **§10** (채팅 안 버튼, GAS 불필요). `config.yaml` → `channel: telegram`

---

## 10. 복약 알림 — 텔레그램 (권장)

카카오와 달리 **채팅 안 「복용 완료 ✅」 버튼** 한 번으로 체크됩니다.

### 10-1. 봇 만들기

1. 텔레그램에서 **@BotFather** 검색 → 채팅 시작
2. `/newbot` 입력
3. 봇 **이름** (표시용, 예: `내 복약 알림`)
4. 봇 **username** (반드시 `bot`으로 끝남, 예: `my_med_alert_bot`)
5. 나온 **토큰** 복사 (`123456789:ABC...`) → `.env` / GitHub Secret **`TELEGRAM_BOT_TOKEN`**

### 10-2. chat_id 확인

1. 방금 만든 **봇** 검색 → 채팅 시작 → **`/start`** 전송
2. Mac 터미널:

```bash
cd ~/job-alert
# .env 에 TELEGRAM_BOT_TOKEN= 넣은 뒤
python scripts/telegram_get_chat_id.py
```

3. 출력된 숫자 → `.env` / GitHub Secret **`TELEGRAM_CHAT_ID`**

### 10-3. config.yaml

```yaml
medication_alert:
  channel: telegram
  message: "아침 약 드실 시간이에요."
```

push 후 GitHub Secrets: `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`

### 10-4. cron-job.org (3개 — 복약용)

| Title | Schedule (KST) | URL 워크플로 |
|-------|----------------|--------------|
| job alert medication 9am | `0 9 * * *` | `medication-alert.yml` |
| job alert medication 11am | `0 11 * * *` | `medication-followup.yml` |
| job alert telegram poll | `*/5 9-12 * * *` | `telegram-poll.yml` |

- **poll**: 9~12시 **5분마다** 버튼 클릭 수신 (채팅 안 체크 반영)
- ADVANCED: §6과 동일 (POST, PAT, `{"ref":"main"}`)

### 10-5. 테스트

1. Actions → **Medication Alert** → Run workflow → 텔레그램에 메시지+버튼
2. **복용 완료 ✅** 탭
3. **Telegram Medication Poll** Run workflow (또는 poll cron 대기) → 메시지가 **✅ (복용 완료)** 로 바뀜

---

## 5. Mac 자동 실행 끄기 (선택)

클라oud만 쓸 거면 Mac 12시 스케줄을 꺼도 됩니다.

```bash
launchctl unload ~/Library/LaunchAgents/com.jobalert.daily.plist
```

---

## 참고

- GitHub Actions 무료 플랜: private 저장소도 월 일정량 무료 (개인용 충분)
- 스케줄은 **몇 분 늦을 수 있음** (GitHub 부하 시)
- 카카오 **refresh token**이 갱신되면 터미널/GitHub Actions 로그에 새 값이 출력될 수 있음 → GitHub Secret도 업데이트
