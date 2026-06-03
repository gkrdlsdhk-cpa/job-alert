#!/usr/bin/env python3
"""카카오 로그인 1회 인증 → refresh token 발급 (최초 1번만 실행)."""

from __future__ import annotations

import os
import sys
from urllib.parse import parse_qs, urlparse

import requests
from dotenv import load_dotenv

from src.kakao_oauth import kakao_client_fields

KAKAO_AUTH_URL = "https://kauth.kakao.com/oauth/authorize"
KAKAO_TOKEN_URL = "https://kauth.kakao.com/oauth/token"


def main() -> int:
    load_dotenv()

    client_id = os.getenv("KAKAO_REST_API_KEY", "").strip()
    redirect_uri = os.getenv("KAKAO_REDIRECT_URI", "http://localhost:8080").strip()

    if not client_id:
        print("오류: .env에 KAKAO_REST_API_KEY를 먼저 넣어 주세요.", file=sys.stderr)
        return 1

    auth_url = (
        f"{KAKAO_AUTH_URL}?response_type=code"
        f"&client_id={client_id}"
        f"&redirect_uri={redirect_uri}"
        "&scope=talk_message"
    )

    print("=== 카카오 1회 로그인 ===\n")
    print("1) 아래 주소를 브라우저 주소창에 붙여넣고 카카오 로그인 + 동의")
    print(f"\n{auth_url}\n")
    print("2) 로그인 후 주소창이 아래처럼 바뀝니다:")
    print("   http://localhost:8080/?code=긴영문숫자...")
    print()
    print("   ⚠️  이때 Safari/Chrome에 「서버에 연결할 수 없음」이 뜨는 것은 정상입니다!")
    print("   localhost:8080 은 우리 Mac에 웹사이트가 없어서 그렇고, 무시하셔도 됩니다.")
    print("   주소창에 code=... 가 보이면 성공입니다. URL 전체를 복사하세요.")
    print()
    print("3) 복사한 URL 전체(또는 code 값만) 터미널에 붙여넣기\n")

    pasted = input("리다이렉트 URL 또는 code 값: ").strip()
    if not pasted:
        print("입력이 비어 있습니다.", file=sys.stderr)
        return 1

    if pasted.startswith("http"):
        query = parse_qs(urlparse(pasted).query)
        code = query.get("code", [""])[0]
    else:
        code = pasted

    if not code:
        print("code 값을 찾지 못했습니다.", file=sys.stderr)
        return 1

    response = requests.post(
        KAKAO_TOKEN_URL,
        data={
            **kakao_client_fields(),
            "grant_type": "authorization_code",
            "redirect_uri": redirect_uri,
            "code": code,
        },
        timeout=15,
    )
    if not response.ok:
        print(f"토큰 발급 실패: {response.status_code} {response.text}", file=sys.stderr)
        if "KOE010" in response.text:
            print(
                "\n💡 KOE010 해결 방법 (둘 중 하나):\n"
                "  A) 카카오 개발자 → 플랫폼 키 → REST API 키 → 클라이언트 시크릿 【사용 안 함】으로 변경\n"
                "  B) 클라이언트 시크릿 【사용】 중이면, 시크릿 코드를 .env의 KAKAO_CLIENT_SECRET= 에 넣기\n"
                "\n설정 변경 후 python kakao_auth.py 를 【처음부터】 다시 실행하세요. (code는 1회용)",
                file=sys.stderr,
            )
        return 1

    payload = response.json()
    refresh_token = payload.get("refresh_token")
    if not refresh_token:
        print("refresh_token이 없습니다. talk_message 동의를 확인해 주세요.", file=sys.stderr)
        return 1

    print("\n=== 성공! .env에 아래 한 줄을 추가/수정하세요 ===\n")
    print(f"KAKAO_REFRESH_TOKEN={refresh_token}")
    print("\n그다음 NOTIFY_VIA=kakao 로 설정하고 python main.py 를 실행하세요.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
