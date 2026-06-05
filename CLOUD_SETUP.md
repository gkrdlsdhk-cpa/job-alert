# 클라oud로 매일 12시 자동 발송 (GitHub Actions)

Mac이 꺼져 있어도 **GitHub 서버**에서 매일 **한국 시간 12:00**에 `main.py`를 실행합니다.

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

### 매일 9시 미국 주식 시세 (테슬라·엔비디아)

GitHub → **Actions** → **Morning Stock Alert** → **Run workflow**

1~2분 후 카카오톡 **나와의 채팅**에 `<주가보고>` 메시지 (가격 + 전일 대비 %).

- 필요 Secret: `KAKAO_REST_API_KEY`, `KAKAO_REFRESH_TOKEN`
- 카카오 **제품 링크 관리** 웹 도메인: `https://m.stock.naver.com`

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
| **Schedule** | Every **10** minutes (또는 cron `*/10 * * * *`) |
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
