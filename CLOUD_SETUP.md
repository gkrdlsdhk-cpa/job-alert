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
git remote add origin https://github.com/본인아이디/job-alert.git
git push -u origin main
```

> `git` 명령이 안 되면: `xcode-select --install` 먼저 실행

---

## 3. GitHub Secrets 등록

GitHub 저장소 → **Settings** → **Secrets and variables** → **Actions** → **New repository secret**

`.env` 파일에 있는 값을 **하나씩** Secret으로 등록합니다.

| Secret 이름 | 필수 | 설명 |
|-------------|------|------|
| `NAVER_CLIENT_ID` | ✅ | 네이버 Client ID |
| `NAVER_CLIENT_SECRET` | ✅ | 네이버 Client Secret |
| `NOTIFY_VIA` | ✅ | `kakao` (카카오만) 또는 `email` 또는 `both` |
| `KAKAO_REST_API_KEY` | 카카오 시 | REST API 키 |
| `KAKAO_REFRESH_TOKEN` | 카카오 시 | refresh token |
| `KAKAO_CLIENT_SECRET` | 선택 | Client Secret **사용** 중일 때만 |
| `EMAIL_FROM` | 이메일 시 | Gmail 주소 |
| `EMAIL_PASSWORD` | 이메일 시 | Gmail 앱 비밀번호 |
| `EMAIL_TO` | 이메일 시 | 받을 메일 |

> **`.env` 파일 자체는 GitHub에 올리지 마세요.** Secret으로만 등록합니다.

---

## 4. 수동 테스트

GitHub 저장소 → **Actions** 탭 → **Daily Job Briefing** → **Run workflow** → **Run workflow**

1~2분 후 카카오톡 **「나와의 채팅」** 또는 Gmail을 확인하세요.

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
