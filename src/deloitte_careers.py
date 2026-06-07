"""딜로이트(안진회계법인) 채용 사이트 — RecruitList 검색 결과."""

from __future__ import annotations

import re
from urllib.parse import quote

import requests
from bs4 import BeautifulSoup

DEFAULT_HOME_URL = "https://join.deloitte.co.kr"
LIST_PATH = "/WiseRecruit2/User/RecruitList.aspx"
VIEW_PATH = "/WiseRecruit2/User/RecruitView.aspx"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "ko-KR,ko;q=0.9",
}

EMPTY_RESULT_TEXT = "검색 결과가 없습니다"


def _encode_exp_type(exp_type: str) -> str:
    """ASP.NET 파서가 ExpType=1,3 을 분리하지 않도록 이중 URL 인코딩."""
    once = quote(exp_type, safe="")
    return quote(once, safe="")


def _build_search_url(
    base_url: str,
    *,
    keyword: str,
    exp_type: str,
    service: str,
    service_dtl: str,
) -> str:
    query = (
        f"Keyword={quote(keyword)}"
        f"&ExpType={_encode_exp_type(exp_type)}"
        f"&Service={quote(service)}"
        f"&ServiceDtl={quote(service_dtl)}"
    )
    return f"{base_url.rstrip('/')}{LIST_PATH}?{query}"


def _parse_list_html(html: str, *, base_url: str) -> list[dict]:
    if EMPTY_RESULT_TEXT in html:
        return []

    soup = BeautifulSoup(html, "html.parser")
    jobs: list[dict] = []

    for row in soup.select("#tblList tbody tr"):
        link_el = row.select_one("a.subject")
        if not link_el:
            continue
        href = link_el.get("href", "")
        match = re.search(r"ridx=(\d+)", href)
        if not match:
            continue

        job_id = match.group(1)
        title = link_el.get_text(strip=True)
        date_el = row.select_one("div.date")
        date_text = re.sub(r"\s+", " ", date_el.get_text(" ", strip=True)) if date_el else ""
        link = f"{base_url.rstrip('/')}{VIEW_PATH}?ridx={job_id}"

        jobs.append(
            {
                "job_id": job_id,
                "title": title,
                "date": date_text,
                "link": link,
                "company": "딜로이트",
            }
        )

    return jobs


def fetch_filtered_jobs(
    base_url: str = DEFAULT_HOME_URL,
    *,
    exp_type: str = "1,3",
    service: str = "AB",
    keyword: str = "",
    service_dtl: str = "",
    max_results: int = 50,
) -> list[dict]:
    """신입 + Service(Tax & Legal) 검색 결과를 조회합니다."""
    session = requests.Session()
    session.headers.update(HEADERS)

    try:
        session.get(
            f"{base_url.rstrip('/')}/WiseRecruit2/ComFiles/Deloitte/MainHome.aspx",
            timeout=25,
        )
        search_url = _build_search_url(
            base_url,
            keyword=keyword,
            exp_type=exp_type,
            service=service,
            service_dtl=service_dtl,
        )
        response = session.get(search_url, timeout=25)
        response.raise_for_status()
    except requests.RequestException:
        return []

    jobs = _parse_list_html(response.text, base_url=base_url)
    return jobs[:max_results]
