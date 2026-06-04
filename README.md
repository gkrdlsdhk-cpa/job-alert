# job-alert — 취업 뉴스·채용 자동 브리핑

회계·Big4 취업 준비생을 위한 **매일 아침 이메일 브리핑** 프로젝트입니다.

- **네이버 뉴스**: 삼일·안진·삼정·한영 등 관심 기업 기사
- **사람인**: 회계법인, 감사, Big4, CPA 키워드 채용 공고
- **한국공인회계사회 구인(수습CPA)**: 신규 공고 시 카카오 실시간 (`kicpa_watch.py`)
- **삼일PwC 정기채용** ([링크](https://pwc.to/2xLHIx4)): 모집 오픈 시 카카오 실시간 (`pwc_watch.py`)
- **알림**: Gmail로 HTML 메일 발송

---

## 0. 맥에서 먼저 할 일 (필수)

터미널을 열고 아래를 입력합니다. (Spotlight에서 `터미널` 검색)

```bash
xcode-select --install
```

창이 뜨면 **설치**를 누릅니다. Python과 Git을 쓰려면 이게 필요합니다.

---

## 1. 프로젝트 폴더로 이동

```bash
cd ~/job-alert
```

---

## 2. 가상환경 만들기 & 패키지 설치

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

`(.venv)` 가 앞에 보이면 성공입니다.

---

## 3. 네이버 검색 API 키 발급 (뉴스용)

1. [네이버 개발자 센터](https://developers.naver.com) 가입/로그인
2. **Application → 애플리케이션 등록**
3. 사용 API: **검색** 선택
4. 등록 후 **Client ID**, **Client Secret** 복사

---

## 4. Gmail 앱 비밀번호 (메일 발송용)

1. Google 계정 → **보안** → **2단계 인증** 켜기
2. **앱 비밀번호** 생성 (이름: job-alert)
3. 16자리 비밀번호 복사 (공백 없이)

---

## 5. 환경 변수 파일 만들기

```bash
cp .env.example .env
```

`.env` 파일을 열어 아래 값을 **본인 것**으로 바꿉니다.

```
NAVER_CLIENT_ID=발급받은_ID
NAVER_CLIENT_SECRET=발급받은_SECRET
EMAIL_FROM=내@gmail.com
EMAIL_PASSWORD=앱비밀번호16자
EMAIL_TO=받을@gmail.com
```

> `.env`는 비밀번호가 들어가므로 다른 사람과 공유하지 마세요.

---

## 6. 관심 기업·키워드 수정 (선택)

`config.yaml` 파일에서 기업 이름, 사람인 키워드, 회계사회 **폴링 주기**(`kicpa.poll_minutes`)를 바꿀 수 있습니다.

---

## 7. 수동으로 한 번 실행해 보기

```bash
cd ~/job-alert
source .venv/bin/activate
python main.py
```

성공하면 **"완료! 메일함을 확인해 주세요."** 가 나오고, Gmail 받은편지함에 브리핑 메일이 옵니다.

---

## 8. 매일 오후 12시 자동 실행 (Mac)

### 8-1. 로그 폴더 만들기

```bash
mkdir -p ~/job-alert/logs
```

### 8-2. 스케줄 파일 복사

```bash
cp ~/job-alert/com.jobalert.daily.plist.example ~/Library/LaunchAgents/com.jobalert.daily.plist
```

`~/Library/LaunchAgents/com.jobalert.daily.plist` 를 열어  
경로가 본인 사용자 이름(`kimhakin`)과 맞는지 확인하세요.

### 8-3. 스케줄 등록

```bash
launchctl load ~/Library/LaunchAgents/com.jobalert.daily.plist
```

매일 **오후 12시**에 Mac이 켜져 있으면 자동 실행됩니다.  
(맥이 꺼져 있으면 그날은 실행되지 않습니다.)

### 시간 변경

plist 파일에서 `<integer>12</integer>` (시), `<integer>0</integer>` (분)을 수정 후:

```bash
launchctl unload ~/Library/LaunchAgents/com.jobalert.daily.plist
launchctl load ~/Library/LaunchAgents/com.jobalert.daily.plist
```

---

## 자주 나는 문제

| 증상 | 해결 |
|------|------|
| `python3: command not found` | 0번 Xcode Command Line Tools 설치 |
| 뉴스가 비어 있음 | `.env`의 네이버 API 키 확인 |
| 메일 발송 실패 | Gmail 2단계 인증 + **앱 비밀번호** 사용 |
| 사람인 공고가 비어 있음 | 사이트 구조 변경 가능 → 메일의 **"사람인에서 더 보기"** 링크 사용 |

---

## 9. 카카오톡으로 받기 (나에게 보내기)

이메일 대신 **카카오톡 '나와의 채팅'** 으로 받을 수 있습니다.

### 9-1. 카카오 개발자 앱 만들기

1. [Kakao Developers](https://developers.kakao.com) 로그인
2. **내 애플리케이션 → 애플리케이션 추가하기**
3. **앱 → 플랫폼 → Web** 추가 → 사이트 도메인: `http://localhost:8080`
4. **앱 → 카카오 로그인** 활성화 → Redirect URI: `http://localhost:8080`
5. **앱 → 카카오톡 메시지** 활성화
6. **앱 키 → REST API 키** 복사

### 9-2. .env 설정

```
NOTIFY_VIA=kakao
KAKAO_REST_API_KEY=REST_API_키
KAKAO_REDIRECT_URI=http://localhost:8080
```

### 9-3. 최초 1회 로그인 (refresh token 발급)

```bash
cd ~/job-alert
source .venv/bin/activate
python kakao_auth.py
```

브라우저에서 카카오 로그인 후, 주소창 URL을 복사해 터미널에 붙여넣으면  
`KAKAO_REFRESH_TOKEN=...` 값이 출력됩니다. `.env`에 저장하세요.

### 9-4. 테스트

```bash
python main.py
```

카카오톡 **'나와의 채팅'** 에 브리핑 메시지가 옵니다.

> 카카오 텍스트 메시지는 한 번에 200자 제한이라, 내용이 길면 [1/3], [2/3]처럼 여러 메시지로 나뉩니다.

---

## 10. 회계사회 수습CPA — 실시간 카카오 알림

**12시 브리핑과 별도**로, 한국공인회계사회 **구인(수습CPA)** 에 새 글이 올라오면 카카오톡 **나와의 채팅**으로 바로 보냅니다. (Gmail 경유 없음)

### 10-1. 카카오 설정

- `.env`에 `KAKAO_REST_API_KEY`, `KAKAO_REFRESH_TOKEN` (README 9번과 동일)
- [Kakao Developers](https://developers.kakao.com) → **제품 링크 관리** → 웹 도메인: `https://www.kicpa.or.kr`

### 10-2. 최초 1회 (기존 공고는 알림 안 함)

```bash
cd ~/job-alert
source .venv/bin/activate
python kicpa_watch.py --seed
```

### 10-3. Mac에서 10분마다 (선택)

```bash
cp ~/job-alert/com.jobalert.kicpa-watch.plist.example ~/Library/LaunchAgents/com.jobalert.kicpa-watch.plist
launchctl load ~/Library/LaunchAgents/com.jobalert.kicpa-watch.plist
```

### 10-4. 삼일PwC 정기채용 모집 오픈 알림

```bash
python pwc_watch.py --seed   # 최초 1회
python pwc_watch.py          # 테스트
```

모집이 열리면 카카오 `[삼일PwC 정기채용]` + 제목 + **채용 보기** 링크 (`https://pwc.to/2xLHIx4`).

### 10-5. Mac 꺼져 있어도 (GitHub Actions)

`CLOUD_SETUP.md` 4번 — **Realtime Job Alerts** (~10분마다, 회계사회 + PwC)

---

## 11. Mac이 꺼져 있어도 매일 12시 자동 실행 (클라우드)

Mac을 끄거나 잠자기 상태여도 **GitHub 서버**에서 매일 **한국 시간 12:00**에 브리핑을 보냅니다.

1. 코드는 이미 GitHub에 올라가 있음: https://github.com/gkrdlsdhk-cpa/job-alert  
2. **`CLOUD_SETUP.md`** 를 열고 **3번 GitHub Secrets**를 `.env` 값대로 **하나씩** 등록  
3. GitHub → **Actions** → **Daily Job Briefing** → **Run workflow** 로 테스트  
4. 클라우드만 쓸 거면 Mac 12시 스케줄 끄기 (`CLOUD_SETUP.md` 5번)

| Mac 스케줄 (8번) | GitHub Actions (10번) |
|------------------|------------------------|
| Mac이 **켜져 있어야** 함 | Mac **꺼져 있어도** 됨 |
| `launchctl` | GitHub Secrets + Actions |

---

## 12. 매일 오전 9시 미국 주식 시세 (카카오)

**테슬라(TSLA)·엔비디아(NVDA)** 시세를 카카오톡 **나와의 채팅**으로 보냅니다. (Yahoo Finance 시세, 전일 대비 등락률)

### 12-1. 필요한 설정

- `.env`에 `KAKAO_REST_API_KEY`, `KAKAO_REFRESH_TOKEN` (README 9번과 동일)
- [Kakao Developers](https://developers.kakao.com) → **제품 링크 관리** → 웹 도메인: `https://finance.yahoo.com`

### 12-2. 테스트

```bash
cd ~/job-alert
source .venv/bin/activate
python stock_alert.py
```

예시 메시지:

```text
[미국주식]
06/04 09:00
테슬라(TSLA) $423.70 +1.88%
엔비디아(NVDA) $214.75 -4.28%
```

### 12-3. Mac에서 매일 9시 (선택)

```bash
cp ~/job-alert/com.jobalert.stock.plist.example ~/Library/LaunchAgents/com.jobalert.stock.plist
launchctl load ~/Library/LaunchAgents/com.jobalert.stock.plist
```

### 12-4. Mac 꺼져 있어도 (GitHub Actions)

GitHub → **Actions** → **Morning Stock Alert** → **Run workflow**  
(스케줄: 한국 시간 **매일 09:00**, Secret은 카카오 2개만 필요 — `CLOUD_SETUP.md` 4번)

종목 변경은 `config.yaml` → `stock_alert.symbols` 에서 수정합니다.

---

## 다음 단계 (나중에)

- [ ] 구글 뉴스 API 추가
- [ ] 링커리어 채용 추가
- [x] 한국공인회계사회 구인(수습CPA) — 실시간 카카오 알림
- [x] 카카오톡 "나에게 보내기" 연동
- [x] 클라우드(GitHub Actions)로 24시간 스케줄 — 설정은 `CLOUD_SETUP.md`
- [x] 매일 9시 테슬라·엔비디아 주가 카카오 알림

궁금한 점은 Cursor 채팅에서 **"job-alert README 3번 도와줘"** 처럼 단계 번호와 함께 물어보세요.
