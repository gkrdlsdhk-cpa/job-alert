"""한국경제 세금 카테고리 — 당일 기사 수집."""

from __future__ import annotations

import re
import time
from datetime import date, datetime
from urllib.parse import urljoin
from zoneinfo import ZoneInfo

import requests
from bs4 import BeautifulSoup

BASE_URL = "https://www.hankyung.com/economy/tax"
KST = ZoneInfo("Asia/Seoul")
DATE_RE = re.compile(r"(\d{4})\.(\d{2})\.(\d{2})")
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "ko-KR,ko;q=0.9",
}


def _today_kst() -> date:
    return datetime.now(KST).date()


def _page_url(page: int) -> str:
    if page <= 1:
        return BASE_URL
    return f"{BASE_URL}?page={page}"


def _parse_display_date(raw: str) -> date | None:
    match = DATE_RE.search(raw or "")
    if not match:
        return None
    return date(int(match.group(1)), int(match.group(2)), int(match.group(3)))


def _fetch_page(page: int) -> str:
    response = requests.get(_page_url(page), headers=HEADERS, timeout=20)
    response.raise_for_status()
    response.encoding = "utf-8"
    return response.text


def parse_articles(html: str) -> list[dict]:
    """세금 카테고리 목록 HTML에서 기사를 파싱합니다."""
    soup = BeautifulSoup(html, "html.parser")
    articles: list[dict] = []

    for row in soup.select("ul.news-list > li"):
        title_link = row.select_one("h2.news-tit a")
        if not title_link:
            continue

        date_el = row.select_one("p.txt-date")
        summary_el = row.select_one("p.lead")
        display_time = date_el.get_text(strip=True) if date_el else ""

        articles.append(
            {
                "source": "hankyung",
                "section": "한국경제 · 세금",
                "title": title_link.get_text(strip=True),
                "link": urljoin(BASE_URL, title_link["href"]),
                "published": display_time,
                "parsed_date": _parse_display_date(display_time),
                "author": "",
                "summary": summary_el.get_text(strip=True) if summary_el else "",
            }
        )

    return articles


def fetch_today_articles(*, max_pages: int = 30) -> list[dict]:
    """세금 카테고리에서 오늘(KST) 올라온 기사를 전부 수집합니다."""
    target = _today_kst()
    seen_links: set[str] = set()
    results: list[dict] = []

    for page in range(1, max_pages + 1):
        items = parse_articles(_fetch_page(page))
        if not items:
            break

        page_has_target = False
        page_has_older = False

        for item in items:
            parsed = item.get("parsed_date")
            if parsed == target:
                page_has_target = True
                link = item["link"]
                if link not in seen_links:
                    seen_links.add(link)
                    results.append(item)
            elif parsed and parsed < target:
                page_has_older = True

        if page_has_older and not page_has_target:
            break
        if page < max_pages:
            time.sleep(0.5)

    return results
