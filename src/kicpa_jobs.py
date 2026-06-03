"""한국공인회계사회 구인(수습CPA) 게시판 수집."""

from __future__ import annotations

import re
import requests
from bs4 import BeautifulSoup

KICPA_BASE = "https://www.kicpa.or.kr"
# 알림마당 > 구인정보 > 구인(수습CPA) 와 동일 목록
KICPA_TRAINEE_LIST_URL = (
    f"{KICPA_BASE}/home/jobOffrSrchNewGnrl/list.face"
    "?listCnt={max_results}&ijEmpSep=all"
)
KICPA_TRAINEE_PORTAL_URL = (
    f"{KICPA_BASE}/portal/default/kicpa/gnb/kr_pc/menu05/menu09/menu07.page"
)
KICPA_DETAIL_URL = f"{KICPA_BASE}/home/jobOffrSrchNewGnrl/detail.face?ijIdNum={{job_id}}"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "ko-KR,ko;q=0.9",
}


def list_page_url(max_results: int = 20) -> str:
    return KICPA_TRAINEE_LIST_URL.format(max_results=max_results)


def detail_url(job_id: str) -> str:
    return KICPA_DETAIL_URL.format(job_id=job_id)


def _job_id_from_onclick(onclick: str | None) -> str:
    if not onclick:
        return ""
    match = re.search(r"fn_detail\(['\"]([^'\"]+)['\"]\)", onclick)
    return match.group(1) if match else ""


def fetch_trainee_cpa_jobs(max_results: int = 10) -> list[dict]:
    """구인(수습CPA) 최신 공고. 실패 시 빈 목록."""
    try:
        response = requests.get(
            list_page_url(max_results),
            headers=HEADERS,
            timeout=20,
        )
        response.raise_for_status()
    except requests.RequestException:
        return []

    soup = BeautifulSoup(response.text, "html.parser")
    jobs: list[dict] = []

    for row in soup.select("table.table_st02 tbody tr"):
        cells = [td.get_text(strip=True) for td in row.find_all("td")]
        if len(cells) < 7:
            continue

        title_el = row.select_one("td.subject a") or row.find("a", href=True)
        if not title_el:
            continue

        title = title_el.get_text(strip=True)
        job_id = _job_id_from_onclick(title_el.get("onclick"))
        link = detail_url(job_id) if job_id else KICPA_TRAINEE_PORTAL_URL

        # 번호 | 제목 | 회사명 | 지역 | 채용상태 | 고용형태 | 등록일 | 조회수
        company = cells[2] if len(cells) > 2 else ""
        region = cells[3] if len(cells) > 3 else ""
        status = cells[4] if len(cells) > 4 else ""
        employment = cells[5] if len(cells) > 5 else ""
        posted = cells[6] if len(cells) > 6 else ""

        condition = " · ".join(
            part for part in (region, status, employment) if part
        )

        jobs.append(
            {
                "job_id": job_id,
                "title": title,
                "company": company,
                "condition": condition,
                "date": posted,
                "link": link,
                "source_keyword": "수습CPA",
            }
        )

        if len(jobs) >= max_results:
            break

    return jobs
