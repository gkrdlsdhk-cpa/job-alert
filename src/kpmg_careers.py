"""삼정 KPMG 채용 사이트 — 신입 탭 공고 목록."""

from __future__ import annotations

import re
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

DEFAULT_LIST_URL = (
    "https://career.kr.kpmg.com/hr/rec/recruit/jobopen/"
    "controller/candidate/JobOpen310WebController/init.hr"
)
SEARCH_PATH = (
    "/hr/rec/recruit/jobopen/controller/candidate/"
    "JobOpen310WebController/search.hr"
)

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "ko-KR,ko;q=0.9",
}

DETAIL_PAGE_RE = re.compile(
    r"goDetailPage\s*\(\s*['\"]([^'\"]+)['\"]\s*,\s*['\"]([^'\"]+)['\"]\s*\)"
)
TOTAL_COUNT_RE = re.compile(r"labelTotalcount.*?html\([\"'](\d+)[\"']\)")


def _search_url(base_url: str) -> str:
    return urljoin(base_url, SEARCH_PATH)


def _parse_search_html(html: str, *, list_url: str) -> tuple[list[dict], int]:
    total = 0
    match = TOTAL_COUNT_RE.search(html)
    if match:
        total = int(match.group(1))

    soup = BeautifulSoup(html, "html.parser")
    jobs: list[dict] = []

    for item in soup.select("li.rec_con_list_li"):
        link_el = item.select_one(".info_box a[onclick]")
        if not link_el:
            continue
        onclick = link_el.get("onclick", "")
        detail_match = DETAIL_PAGE_RE.search(onclick)
        if not detail_match:
            continue

        job_id, receive_div = detail_match.group(1), detail_match.group(2)
        title_el = item.select_one("p.tit")
        date_el = item.select_one("span.date")
        title = title_el.get_text(strip=True) if title_el else ""
        date = re.sub(r"\s+", " ", date_el.get_text(" ", strip=True)) if date_el else ""

        jobs.append(
            {
                "job_id": job_id,
                "title": title,
                "date": date,
                "link": list_url,
                "receive_div_cd": receive_div,
                "company": "삼정KPMG",
            }
        )

    return jobs, total


def fetch_new_graduate_jobs(
    list_url: str = DEFAULT_LIST_URL,
    *,
    receive_div_cd: str = "N",
    max_results: int = 50,
) -> list[dict]:
    """신입 탭 공고를 조회합니다. 실패 시 빈 목록."""
    session = requests.Session()
    session.headers.update(
        {
            **HEADERS,
            "Referer": list_url,
        }
    )

    try:
        init_response = session.get(list_url, timeout=25)
        init_response.raise_for_status()
    except requests.RequestException:
        return []

    search_url = _search_url(list_url)
    page_size = min(max(max_results, 1), 50)
    all_jobs: list[dict] = []
    seen: set[str] = set()
    page = 1
    total = 0

    while len(all_jobs) < max_results:
        payload = {
            "maxresults": str(page_size),
            "maxlinks": "10",
            "currentpage": str(page),
            "tab_receive_div_cd": receive_div_cd,
            "receive_div_cd": "",
            "jobopen_id": "",
            "sortType": "",
            "sel_field_job": "",
        }
        try:
            response = session.post(search_url, data=payload, timeout=25)
            response.raise_for_status()
        except requests.RequestException:
            break

        jobs, total = _parse_search_html(response.text, list_url=list_url)
        if not jobs:
            break

        for job in jobs:
            job_id = job["job_id"]
            if job_id in seen:
                continue
            seen.add(job_id)
            all_jobs.append(job)
            if len(all_jobs) >= max_results:
                break

        if len(all_jobs) >= total or len(all_jobs) >= max_results:
            break
        page += 1
        if page > 20:
            break

    return all_jobs
