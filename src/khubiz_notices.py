"""경희대 경영대학 청현재 공지사항 — 키워드 매칭 공지 수집."""

from __future__ import annotations

import re
from urllib.parse import urlencode, urljoin

import requests
from bs4 import BeautifulSoup

DEFAULT_LIST_URL = (
    "https://kbiz.khu.ac.kr/biz_kor/user/bbs/BMSR00040/list.do"
    "?menuNo=14500123&boardType=&pageIndex=1&searchCondition="
    "&searchKeyword=&userDisplayCount=10"
)
BASE_URL = "https://kbiz.khu.ac.kr"
VIEW_ID_RE = re.compile(r"view\(['\"]?(\d+)['\"]?\)")
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "ko-KR,ko;q=0.9",
}


def _notice_link(board_id: str) -> str:
    params = urlencode({"menuNo": "14500123", "boardId": board_id})
    return f"{BASE_URL}/biz_kor/user/bbs/BMSR00040/view.do?{params}"


def _parse_notice_row(row) -> dict | None:
    link_el = row.select_one("a[href]")
    if not link_el:
        return None

    href = link_el.get("href", "")
    match = VIEW_ID_RE.search(href)
    if match:
        notice_id = match.group(1)
        link = _notice_link(notice_id)
    elif "view.do" in href:
        notice_id = href
        link = urljoin(BASE_URL, href)
    else:
        return None

    cells = [cell.get_text(" ", strip=True) for cell in row.select("td")]
    title = link_el.get_text(" ", strip=True)
    date = cells[-1] if cells else ""
    category = cells[1] if len(cells) >= 3 else ""

    return {
        "job_id": notice_id,
        "title": title,
        "date": date,
        "category": category,
        "link": link,
        "company": "경희대 경영대학",
    }


def fetch_notices(list_url: str = DEFAULT_LIST_URL, *, max_results: int = 20) -> list[dict]:
    response = requests.get(list_url, headers=HEADERS, timeout=20)
    response.raise_for_status()
    response.encoding = "utf-8"

    soup = BeautifulSoup(response.text, "html.parser")
    notices: list[dict] = []
    seen: set[str] = set()
    for row in soup.select("tbody tr"):
        notice = _parse_notice_row(row)
        if not notice:
            continue
        notice_id = notice["job_id"]
        if notice_id in seen:
            continue
        seen.add(notice_id)
        notices.append(notice)
        if len(notices) >= max_results:
            break
    return notices


def filter_notices_by_keywords(notices: list[dict], keywords: list[str]) -> list[dict]:
    normalized_keywords = [keyword.strip() for keyword in keywords if keyword.strip()]
    if not normalized_keywords:
        return notices
    return [
        notice
        for notice in notices
        if any(keyword in notice.get("title", "") for keyword in normalized_keywords)
    ]
