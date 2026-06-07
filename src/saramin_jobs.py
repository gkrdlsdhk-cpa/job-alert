"""사람인 채용 공고 검색 (공개 검색 페이지 기반)."""

from __future__ import annotations

import re
from urllib.parse import quote_plus

import requests
from bs4 import BeautifulSoup


SARAMIN_SEARCH_URL = "https://www.saramin.co.kr/zf_user/search/recruit"
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "ko-KR,ko;q=0.9",
}


def search_url(keyword: str) -> str:
    return f"{SARAMIN_SEARCH_URL}?searchword={quote_plus(keyword)}&recruitPageCount=20"


def _extract_rec_idx(link: str) -> str:
    if "rec_idx=" not in link:
        return ""
    return link.split("rec_idx=")[1].split("&")[0]


def _parse_item(item, *, source_keyword: str) -> dict | None:
    title_el = item.select_one("h2.job_tit a")
    company_el = item.select_one("strong.corp_name a")
    condition_el = item.select_one("div.job_condition")
    date_el = item.select_one("span.date")

    if not title_el:
        return None

    title = title_el.get_text(strip=True)
    link = title_el.get("href", "")
    if link and not link.startswith("http"):
        link = "https://www.saramin.co.kr" + link

    return {
        "title": title,
        "company": company_el.get_text(strip=True) if company_el else "",
        "condition": re.sub(r"\s+", " ", condition_el.get_text(" ", strip=True))
        if condition_el
        else "",
        "date": date_el.get_text(strip=True) if date_el else "",
        "link": link,
        "job_id": _extract_rec_idx(link),
        "source_keyword": source_keyword,
    }


def fetch_jobs(keyword: str, max_results: int = 5) -> list[dict]:
    """키워드로 사람인 채용 공고를 검색합니다. 실패 시 빈 목록."""
    try:
        response = requests.get(
            search_url(keyword),
            headers=HEADERS,
            timeout=20,
        )
        response.raise_for_status()
    except requests.RequestException:
        return []

    soup = BeautifulSoup(response.text, "html.parser")
    jobs: list[dict] = []

    for item in soup.select("div.item_recruit"):
        job = _parse_item(item, source_keyword=keyword)
        if not job:
            continue
        jobs.append(job)
        if len(jobs) >= max_results:
            break

    return jobs


def fetch_company_jobs(
    search_keyword: str,
    company_name: str,
    *,
    max_results: int = 50,
    exclude_title_contains: list[str] | None = None,
) -> list[dict]:
    """기업명 검색 후 회사명이 정확히 일치하는 공고만 반환."""
    excludes = exclude_title_contains or []
    try:
        response = requests.get(
            search_url(search_keyword),
            headers=HEADERS,
            timeout=20,
        )
        response.raise_for_status()
    except requests.RequestException:
        return []

    soup = BeautifulSoup(response.text, "html.parser")
    jobs: list[dict] = []

    for item in soup.select("div.item_recruit"):
        job = _parse_item(item, source_keyword=search_keyword)
        if not job or not job.get("job_id"):
            continue
        if job["company"] != company_name:
            continue
        if any(token in job["title"] for token in excludes):
            continue
        jobs.append(job)
        if len(jobs) >= max_results:
            break

    return jobs


def fetch_all_company_jobs(
    companies: list[dict],
    *,
    max_results_per_company: int = 50,
    exclude_title_contains: list[str] | None = None,
) -> list[dict]:
    """여러 기업 공고 수집. rec_idx 기준 전역 중복 제거."""
    seen: set[str] = set()
    all_jobs: list[dict] = []

    for entry in companies:
        search_keyword = entry["search_keyword"]
        company_name = entry["company_name"]
        jobs = fetch_company_jobs(
            search_keyword,
            company_name,
            max_results=max_results_per_company,
            exclude_title_contains=exclude_title_contains,
        )
        for job in jobs:
            job_id = job["job_id"]
            if job_id in seen:
                continue
            seen.add(job_id)
            all_jobs.append(job)

    return all_jobs


def fetch_all_jobs(keywords: list[str], max_results_per_keyword: int) -> dict[str, list[dict]]:
    """키워드별 채용 공고 + 검색 페이지 링크."""
    results: dict[str, list[dict]] = {}
    for keyword in keywords:
        jobs = fetch_jobs(keyword, max_results=max_results_per_keyword)
        results[keyword] = jobs
    return results
