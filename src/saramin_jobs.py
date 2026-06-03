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
        title_el = item.select_one("h2.job_tit a")
        company_el = item.select_one("strong.corp_name a")
        condition_el = item.select_one("div.job_condition")
        date_el = item.select_one("span.date")

        if not title_el:
            continue

        title = title_el.get_text(strip=True)
        link = title_el.get("href", "")
        if link and not link.startswith("http"):
            link = "https://www.saramin.co.kr" + link

        jobs.append(
            {
                "title": title,
                "company": company_el.get_text(strip=True) if company_el else "",
                "condition": re.sub(r"\s+", " ", condition_el.get_text(" ", strip=True))
                if condition_el
                else "",
                "date": date_el.get_text(strip=True) if date_el else "",
                "link": link,
                "source_keyword": keyword,
            }
        )

        if len(jobs) >= max_results:
            break

    return jobs


def fetch_all_jobs(keywords: list[str], max_results_per_keyword: int) -> dict[str, list[dict]]:
    """키워드별 채용 공고 + 검색 페이지 링크."""
    results: dict[str, list[dict]] = {}
    for keyword in keywords:
        jobs = fetch_jobs(keyword, max_results=max_results_per_keyword)
        results[keyword] = jobs
    return results
