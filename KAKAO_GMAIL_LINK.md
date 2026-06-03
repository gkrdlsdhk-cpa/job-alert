# 카카오톡 버튼 → Gmail 연결 설정

카카오 메시지에서 **「모바일에서 확인해주세요」** 만 보이거나 버튼이 **job-alert** 로만 보이면,
Gmail 링크 도메인이 카카오에 **등록되지 않은 것**입니다.

---

## 1. 카카오 개발자에서 웹 도메인 등록 (필수)

1. [Kakao Developers](https://developers.kakao.com) → **job-alert** 앱
2. 왼쪽 **앱** → **제품 링크 관리**
3. **웹 도메인** → **웹 도메인 등록** (또는 추가)
4. 아래 주소 입력:

```
https://mail.google.com
```

5. **저장**

> 카카오는 **등록된 도메인**으로만 메시지 링크/버튼 이동을 허용합니다.

---

## 2. 코드 push + Actions 실행

```bash
cd ~/job-alert
git add .
git commit -m "Use Kakao feed template for Gmail link button"
git push
```

GitHub → **Actions** → **Daily Job Briefing** → **Run workflow**

---

## 3. 확인

| 기기 | 기대 동작 |
|------|-----------|
| **폰 카카오톡** | **브리핑 메일 보기** 버튼 → Gmail(브리핑 검색) |
| **PC 카카오톡** | 버튼 클릭 → **브라우저**에서 Gmail 열림 (정상) |

PC 카카오톡 안에서 Gmail 앱처럼 열리지는 않고, **브라우저로 Gmail**이 열리는 게 정상입니다.

---

## 4. 그래도 안 되면

- Gmail 앱/브라우저에 **gkrdlsdhk@khu.ac.kr** 로그인 확인
- 메일 **스팸함** 확인
- 카카오 **제품 링크 관리**에 `https://mail.google.com` 이 **정확히** 들어갔는지 재확인
