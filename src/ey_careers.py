"""EY한영(한영회계법인) 채용 사이트 — 공채 탭 공고 목록."""

from __future__ import annotations

from urllib.parse import urlparse

import requests

API_BASE = "https://api-recruiter.recruiter.co.kr"
DEFAULT_HOME_URL = "https://eycareers-kr.recruiter.co.kr/career/home"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json",
    "Content-Type": "application/json",
    "Accept-Language": "ko-KR,ko;q=0.9",
}


def _api_headers(api_prefix: str, *, home_url: str) -> dict[str, str]:
    origin = f"https://{api_prefix}"
    return {
        **HEADERS,
        "prefix": api_prefix,
        "Origin": origin,
        "Referer": home_url,
    }


def _site_origin(home_url: str) -> str:
    parsed = urlparse(home_url)
    return f"{parsed.scheme}://{parsed.netloc}"


def _format_date(item: dict) -> str:
    start = str(item.get("startDateTime") or "")
    end = item.get("endDateTime")
    if end:
        return f"{start[:10]} ~ {str(end)[:10]}"
    if start:
        return start[:10]
    return "상시"


def fetch_classification_tag_sn(
    api_prefix: str,
    *,
    home_url: str,
    tag_name: str,
) -> int | None:
    """설정 API에서 분류 태그(공채 등) 번호를 조회합니다."""
    try:
        response = requests.post(
            f"{API_BASE}/position/v2/jobflex/setting",
            headers=_api_headers(api_prefix, home_url=home_url),
            json={},
            timeout=25,
        )
        response.raise_for_status()
    except requests.RequestException:
        return None

    tag_list = response.json().get("tag", {}).get("tagList") or []
    for tag in tag_list:
        if str(tag.get("tagName", "")).strip() == tag_name:
            return int(tag["tagSn"])
    return None


def fetch_open_recruitment_jobs(
    home_url: str = DEFAULT_HOME_URL,
    *,
    api_prefix: str | None = None,
    classification_tag_name: str = "공채",
    max_results: int = 50,
) -> list[dict]:
    """공채 탭 공고를 조회합니다. 실패 시 빈 목록."""
    prefix = api_prefix or urlparse(home_url).netloc
    tag_sn = fetch_classification_tag_sn(
        prefix,
        home_url=home_url,
        tag_name=classification_tag_name,
    )
    if tag_sn is None:
        return []

    site_origin = _site_origin(home_url)
    headers = _api_headers(prefix, home_url=home_url)
    page_size = min(max(max_results, 1), 50)
    all_jobs: list[dict] = []
    page = 1

    while len(all_jobs) < max_results:
        payload = {
            "pageableRq": {
                "page": page,
                "size": page_size,
                "sort": ["CREATED_DATE_TIME"],
            },
            "filter": {
                "keyword": "",
                "tagSnList": [tag_sn],
                "jobGroupSnList": [],
                "careerTypeList": [],
                "regionSnList": [],
                "submissionStatusList": [],
                "openStatusList": ["OPEN"],
                "resumeLanguageTypeList": [],
            },
        }
        try:
            response = requests.post(
                f"{API_BASE}/position/v1/jobflex",
                headers=headers,
                json=payload,
                timeout=25,
            )
            response.raise_for_status()
        except requests.RequestException:
            break

        data = response.json()
        items = data.get("list") or []
        if not items:
            break

        for item in items:
            position_sn = item.get("positionSn")
            if position_sn is None:
                continue
            job_id = str(position_sn)
            all_jobs.append(
                {
                    "job_id": job_id,
                    "title": str(item.get("title", "")).strip(),
                    "date": _format_date(item),
                    "link": f"{site_origin}/career/jobs/{job_id}",
                    "company": "EY한영",
                    "classification_code": str(item.get("classificationCode", "")),
                }
            )
            if len(all_jobs) >= max_results:
                break

        pagination = data.get("pagination") or {}
        total_pages = int(pagination.get("totalPages") or 1)
        if page >= total_pages:
            break
        page += 1
        if page > 20:
            break

    return all_jobs
