"""카카오 OAuth 공통 설정."""

from __future__ import annotations

import os


def kakao_client_fields() -> dict[str, str]:
    """토큰 요청에 넣을 client_id (+ client_secret이 있으면 함께)."""
    client_id = os.getenv("KAKAO_REST_API_KEY", "").strip()
    fields: dict[str, str] = {"client_id": client_id}

    client_secret = os.getenv("KAKAO_CLIENT_SECRET", "").strip()
    if client_secret:
        fields["client_secret"] = client_secret

    return fields
