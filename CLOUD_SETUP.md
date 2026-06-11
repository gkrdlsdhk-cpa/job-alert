# 클라oud 자동 발송 (GitHub Actions + cron-job.org)

Mac이 꺼져 있어도 **cron-job.org**가 정해진 시간에 GitHub Actions를 호출합니다.

| 브리핑 | 시간 (KST) | 스크립트 |
|--------|------------|----------|
| 회계법인 뉴스 | **23:00** | `firm_news_briefing.py` |

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
| `EMAIL_FROM` | ✅ | Gmail 주소 |
| `EMAIL_PASSWORD` | ✅ | Gmail 앱 비밀번호 |
| `EMAIL_TO` | ✅ | 받을 Gmail (본인 주소) |
| `TELEGRAM_BOT_TOKEN` | 텔레그램 알림 시 | BotFather 토큰 (**§10**) |
| `TELEGRAM_CHAT_ID` | 텔레그램 알림 시 | 본인 chat id (**§10**) |
| `KAKAO_REST_API_KEY` | 카카오 알림 시 | REST API 키 (실시간 공고·`firm_news_briefing` channel: kakao) |
| `KAKAO_REFRESH_TOKEN` | 카카오 알림 시 | refresh token |
| `KAKAO_CLIENT_SECRET` | 선택 | Client Secret **사용** 중일 때만 |

> **`.env` 파일 자체는 GitHub에 올리지 마세요.** Secret으로만 등록합니다.

---

## 4. 수동 테스트

### 회계법인 뉴스 (매일 23시)

GitHub → **Actions** → **회계법인 뉴스** → **Run workflow**

1~2분 후:
- **Gmail** `[회계법인 뉴스]` 메일 (Big4·회계법인 당일 기사)
- **텔레그램** 「브리핑 메일 보기」 알림

- 필요 Secret: 네이버 2개 + Gmail 3개 + `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`
- **매일 23:00 KST** 자동 실행 → **§8-1 cron-job.org**

### 오늘의 tax 브리핑

GitHub → **Actions** → **오늘의 tax 브리핑** → **Run workflow**

1~2분 후 Gmail `[오늘의 tax 브리핑]` 메일 (TaxWatch + 이택스뉴스 + 한국경제 세금 + 택스타임스 + 일간NTN) + 텔레그램 「브리핑 메일 보기」 알림.

- 필요 Secret: Gmail 3개 + `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`
- 자동 실행: **§8-4** cron-job.org **매일 23:00 KST** (GitHub 내장 schedule 없음)

### 매일 9시 미국 주식 시세 (나스닥·테슬라·엔비디아)

GitHub → **Actions** → **Morning Stock Alert** → **Run workflow**

1~2분 후 텔레그램에 `📈 <주가보고>` 메시지 (가격 + 전일 대비 %, 네이버 증권 버튼).

- 필요 Secret: `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID` (복약 알림과 동일 봇 가능, **§10**)
- `config.yaml` → `stock_alert.channel: telegram` (기본값)
- 카카오로 받으려면 `channel: kakao` + `KAKAO_REST_API_KEY`, `KAKAO_REFRESH_TOKEN`
- **매일 09:00 KST** 자동 실행 → **§7 cron-job.org** 권장 (GitHub 내장 9시 cron은 자주 스킵됨)

### 실시간 카카오 알림 (회계사회 + 삼일PwC + 사람인 Big4 + 삼정KPMG + EY한영 + 딜로이트)

GitHub → **Actions** → **Realtime Job Alerts** → **Run workflow**

| 대상 | 알림 시점 | 카카오 메시지 |
|------|-----------|----------------|
| 회계사회 구인(수습CPA) | 신규 공고 또는 **같은 ID에 제목·등록일 변경(재게시)** | `[회계사회 수습CPA 신규]` / `[재게시]…` + 공고 보기 |
| 삼일PwC 정기채용 | 모집 오픈(지원 링크·모집 중 문구 등장) | `[삼일PwC 정기채용]` + 채용 보기 |
| 사람인 Big4 (삼일·삼정KPMG·안진·한영) | **회사명 일치** 신규 공고 (`경력` 제목 제외) | `[사람인 {회사명}]` + 공고 보기 |
| 삼정KPMG 채용 사이트 | **신입** 탭 신규·재게시 공고 | `[삼정KPMG 신입]` + 채용 보기 |
| EY한영(한영회계법인) 채용 사이트 | **수시** 탭 신규·재게시 공고 | `[EY한영 수시]` + 공고 보기 |
| 딜로이트(안진회계법인) 채용 사이트 | **신입** + **Tax & Legal** 검색 결과 | `[딜로이트 Tax&Legal]` + 공고 보기 |

- **첫 실행(또는 캐시 없음)**: 그때 목록에 있던 공고만 등록 (알림 없음). **그 직후 올라온 글부터** 알림
- 사람인: `config.yaml` → `saramin_watch.companies` (검색어 = 사람인 **회사명** 정확 일치)
- 삼정KPMG: `config.yaml` → `kpmg_watch` (`receive_div_cd: N` = 신입 탭)
- EY한영: `config.yaml` → `ey_watch` (`classification_tag_name: 수시`)
- 딜로이트: `config.yaml` → `deloitte_watch` (`exp_type: "1,3"`, `service: AB`)
- 놓친 공고가 있으면 Actions 로그에 `기준선 등록` / `신규 N건` 확인
- **이후 ~10분마다** 자동 확인 → **§6 외부 스케줄러** 권장 (GitHub 내장 10분 cron은 자주 스킵됨)
- **watch 하나가 실패**해도 나머지는 계속 확인 (`realtime_watch.py`). 실패 시 `[Job Alert 오류]` 카카오 + Actions run 링크
- 필요 Secret: `KAKAO_REST_API_KEY`, `KAKAO_REFRESH_TOKEN`
- 카카오 **제품 링크 관리** 웹 도메인: `https://www.kicpa.or.kr`, `https://www.pwc.com`, `https://www.saramin.co.kr`, `https://career.kr.kpmg.com`, `https://eycareers-kr.recruiter.co.kr`, `https://join.deloitte.co.kr`

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
- GitHub 내장 `schedule`은 사용하지 않음 — **cron-job.org만** 사용

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

### 7-3. 하루 1회

- `stock_alert.py`가 `stock_daily_sent.json`으로 **당일 중복 발송** 방지 (TEST RUN·수동 실행도 스킵)

### 7-4. 주말

- 주가 알림은 **매일 9시** (`0 9 * * *`) — 주말에도 전일 종가 기준으로 보냄
- 실시간 공고(§6)만 평일(`1-5`)로 끄면 됨

---

## 8. 회계법인 뉴스 — cron-job.org (권장)

GitHub 내장 cron은 **몇 시간 늦게** 돌 수 있습니다. **cron-job.org**에서 호출하세요.

### 8-1. 회계법인 뉴스 (23시)

**로컬 테스트**

```bash
chmod +x ~/job-alert/scripts/trigger-firm-news-briefing.sh
GITHUB_TOKEN=github_pat_여기에_붙여넣기 ~/job-alert/scripts/trigger-firm-news-briefing.sh
```

| 항목 | 값 |
|------|-----|
| **Title** | `job alert firm news 11pm` |
| **URL** | `https://api.github.com/repos/gkrdlsdhk-cpa/job-alert/actions/workflows/firm-news-briefing.yml/dispatches` |
| **Schedule** | `0 23 * * *` |
| **Time zone** | `Asia/Seoul` |
| **Request method** | **POST** |
| **Headers** | §6과 동일 |
| **Request body** | `{"ref":"main"}` |

### 8-3. cron-job 요약 (복약은 §10)

| Title | Schedule (KST) | 워크플로 |
|-------|----------------|----------|
| job alert realtime | `*/10 9-18 * * 1-5` (평일 9~19시 10분) | `kicpa-watch.yml` |
| job alert stock 9am | `0 9 * * *` (매일 9시) | `stock-alert.yml` |
| job alert medication 10am | `0 10 * * *` (매일 10시) | `medication-alert.yml` |
| job alert firm news 11pm | `0 23 * * *` (매일 23시) | `firm-news-briefing.yml` |
| job alert taxwatch 11pm | `0 23 * * *` (매일 23시) | `taxwatch-briefing.yml` |

텔레그램만 끄려면 `config.yaml` → `firm_news_briefing.channel: email`.

### 8-4. 오늘의 tax 브리핑 (매일 23시)

[TaxWatch 최신뉴스](https://www.taxwatch.co.kr/search), [이택스뉴스](https://www.etaxnews.com/) **세정(내국세·지방세)·유권해석**, [한국경제 세금](https://www.hankyung.com/economy/tax), [택스타임스 내국세·지방세](https://www.taxtimes.co.kr/news/section_list_all.html?sec_no=416), [일간NTN 유권해석·조세행정·오피니언](https://www.intn.co.kr/news/articleList.html?sc_section_code=S1N5&view_type=sm)에서 **오늘(KST) 올라온 기사**를 Gmail HTML로 보내고, **텔레그램**으로 「브리핑 메일 보기」 알림을 보냅니다.

> GitHub Actions **내장 schedule은 사용하지 않습니다.** 다른 알림(주가·브리핑)과 같이 **cron-job.org**만 씁니다.

**로컬 테스트**

```bash
cd ~/job-alert && source .venv/bin/activate
python taxwatch_briefing.py
```

**cron-job.org** — 잡 하나 더 추가 (§6과 동일 PAT·POST·Headers·body)

| 항목 | 값 |
|------|-----|
| **Title** | `job alert taxwatch 11pm` |
| **URL** | `https://api.github.com/repos/gkrdlsdhk-cpa/job-alert/actions/workflows/taxwatch-briefing.yml/dispatches` |
| **Schedule** | Custom crontab: `0 23 * * *` |
| **Time zone** | `Asia/Seoul` |
| **Request method** | **POST** |
| **Headers** | §6과 동일 (`Accept`, `Authorization`, `X-GitHub-Api-Version`, `Content-Type`) |
| **Request body** | `{"ref":"main"}` |

**SAVE** → **TEST RUN** → `204` → 1~2분 후 텔레그램 알림 확인.

필요 Secret: `EMAIL_FROM`, `EMAIL_PASSWORD`, `EMAIL_TO`, `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`  
(복약·주가와 **동일 텔레그램 봇** 사용 가능)

---

## 10. 텔레그램 — 복약·주가·취업·tax 브리핑 (권장)

복약 알림은 **텔레그램 전용**입니다. 채팅 안 **「복용 완료 ✅」** 버튼으로 체크합니다.  
주가·회계법인·tax 브리핑(`stock_alert`, `firm_news_briefing`, `taxwatch_briefing` → `channel: telegram`)도 **같은 봇·chat_id**로 받을 수 있습니다.

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
  message: "아침 약 드실 시간이에요."

firm_news_briefing:
  channel: telegram

stock_alert:
  channel: telegram

taxwatch_briefing:
  channel: telegram
```

push 후 GitHub Secrets: `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`

### 10-4. Webhook — 버튼 즉시 반영 (권장)

GitHub Actions 감시 대신 **Cloudflare Workers Webhook**을 쓰면 맥이 꺼져 있어도 버튼 탭 **1~2초 안**에 **복용 완료**로 바뀝니다.

#### 10-4-1. Cloudflare Worker 배포

1. [Cloudflare](https://dash.cloudflare.com) 가입 → **Workers & Pages** → **Create**
2. **Hello World** 템플릿으로 Worker 생성
3. 코드 편집기에 `workers/telegram-webhook/worker.js` 내용 **전부 붙여넣기** → **Deploy**
4. Worker URL 복사 (예: `https://job-alert-telegram-webhook.kim.workers.dev`)
5. **Settings** → **Variables** → **Secrets**:
   - `TELEGRAM_BOT_TOKEN` = BotFather 토큰
   - `WEBHOOK_SECRET` = 임의 문자열 (예: `my-random-secret-123`) — 선택이지만 권장

> Wrangler CLI 사용 시: `workers/telegram-webhook/wrangler.toml.example` 참고

#### 10-4-2. Webhook 등록 (Mac 터미널, 1회)

`.env`에 추가:

```
TELEGRAM_USE_WEBHOOK=1
TELEGRAM_WEBHOOK_URL=https://job-alert-telegram-webhook.kim.workers.dev
TELEGRAM_WEBHOOK_SECRET=my-random-secret-123
```

```bash
cd ~/job-alert
source .venv/bin/activate
python scripts/telegram_set_webhook.py
python scripts/telegram_set_webhook.py --info   # url 이 Worker 주소인지 확인
```

> Webhook 등록 후 버튼 처리는 **Worker만** 담당합니다.

#### 10-4-3. cron-job.org — 알림 1개만

| Title | Schedule (KST) | URL 워크플로 |
|-------|----------------|--------------|
| job alert medication 10am | `0 10 * * *` | `medication-alert.yml` |

- **역할**: 매일 정해진 시간에 텔레그램 알림만 발송 (9시·10시 등 원하는 시각으로 설정)
- **버튼 처리**: Worker Webhook이 **24시간 즉시** 처리 (Followup·Poll 워크플로 불필요)
- ADVANCED: §6과 동일 (POST, PAT, `{"ref":"main"}`)

### 10-5. 테스트

1. Actions → **Medication Alert** → Run workflow → 텔레그램에 메시지+버튼
2. **먹었어요 ✅** 탭
3. **1~2초 안** 메시지가 **✅ … 복용 완료** 로 바뀌면 성공

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
