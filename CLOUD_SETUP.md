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
- **이후 ~10분마다** 자동 확인
- 필요 Secret: `KAKAO_REST_API_KEY`, `KAKAO_REFRESH_TOKEN`
- 카카오 **제품 링크 관리** 웹 도메인: `https://www.kicpa.or.kr`, `https://www.pwc.com`

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
