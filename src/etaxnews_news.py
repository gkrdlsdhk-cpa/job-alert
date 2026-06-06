"""이택스뉴스 — 세정(내국세·지방세)·유권해석 당일 기사 수집."""

from __future__ import annotations

import re
import time
from datetime import date, datetime
from urllib.parse import urljoin
from zoneinfo import ZoneInfo

import requests
from bs4 import BeautifulSoup

BASE_URL = "https://www.etaxnews.com"
KST = ZoneInfo("Asia/Seoul")
DATE_SHORT_RE = re.compile(r"^(\d{2})-(\d{2})\b")
DATE_FULL_RE = re.compile(r"^(\d{4})-(\d{2})-(\d{2})\b")
PAGE_DATE_RE = re.compile(r"발행일:\s*(\d{4})-(\d{2})-(\d{2})")
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
}

DEFAULT_FEEDS: list[dict[str, str]] = [
    {
        "section": "내국세",
        "list_url": (
            f"{BASE_URL}/news/articleList.html"
            "?sc_section_code=S1N1&sc_sub_section_code=S2N8&view_type=sm"
        ),
    },
    {
        "section": "지방세",
        "list_url": (
            f"{BASE_URL}/news/articleList.html"
            "?sc_section_code=S1N1&sc_sub_section_code=S2N9&view_type=sm"
        ),
    },
    {
        "section": "유권해석",
        "list_url": (
            f"{BASE_URL}/news/articleList.html?sc_section_code=S1N2&view_type=sm"
        ),
    },
]


def _today_kst() -> date:
    return datetime.now(KST).date()


def _page_year(html: str) -> int:
    match = PAGE_DATE_RE.search(html)
    if match:
        return int(match.group(1))
    return _today_kst().year


def _parse_list_date(raw: str, *, page_year: int) -> date | None:
    text = (raw or "").strip()
    match = DATE_FULL_RE.match(text)
    if match:
        return date(int(match.group(1)), int(match.group(2)), int(match.group(3)))

    match = DATE_SHORT_RE.match(text)
    if match:
        return date(page_year, int(match.group(1)), int(match.group(2)))
    return None


def _page_url(list_url: str, page: int) -> str:
    if page <= 1:
        return list_url
    joiner = "&" if "?" in list_url else "?"
    return f"{list_url}{joiner}page={page}"


def _fetch_page(url: str) -> str:
    response = requests.get(url, headers=HEADERS, timeout=20)
    response.raise_for_status()
    response.encoding = "utf-8"
    return response.text


def parse_articles(html: str, *, section: str) -> list[dict]:
    """목록 HTML에서 기사를 파싱합니다."""
    soup = BeautifulSoup(html, "html.parser")
    page_year = _page_year(html)
    articles: list[dict] = []

    for row in soup.select("article.altlist-body li.altlist-text-item"):
        title_link = row.select_one("h2.altlist-subject a")
        if not title_link:
            continue

        info_items = row.select(".altlist-info-item")
        infos = [item.get_text(strip=True) for item in info_items]
        display_time = infos[-1] if infos else ""
        author = infos[-2] if len(infos) >= 2 else ""

        articles.append(
            {
                "source": "etaxnews",
                "section": section,
                "title": title_link.get_text(strip=True),
                "link": urljoin(BASE_URL, title_link["href"]),
                "published": display_time,
                "parsed_date": _parse_list_date(display_time, page_year=page_year),
                "author": author,
                "summary": "",
            }
        )

    return articles


def fetch_today_for_feed(
    feed: dict[str, str],
    *,
    max_pages: int = 30,
    seen_links: set[str] | None = None,
) -> list[dict]:
    """피드 하나에서 오늘(KST) 기사를 수집합니다."""
    target = _today_kst()
    section = feed["section"]
    list_url = feed["list_url"]
    seen = seen_links if seen_links is not None else set()
    results: list[dict] = []

    for page in range(1, max_pages + 1):
        items = parse_articles(_fetch_page(_page_url(list_url, page)), section=section)
        if not items:
            break

        page_has_target = False
        page_has_older = False

        for item in items:
            parsed = item.get("parsed_date")
            if parsed == target:
                page_has_target = True
                link = item["link"]
                if link not in seen:
                    seen.add(link)
                    results.append(item)
            elif parsed and parsed < target:
                page_has_older = True

        if page_has_older and not page_has_target:
            break
        if page < max_pages:
            time.sleep(0.5)

    return results


def fetch_today_by_section(
    feeds: list[dict[str, str]] | None = None,
    *,
    max_pages: int = 30,
) -> dict[str, list[dict]]:
    """내국세·지방세·유권해석 당일 기사를 섹션별로 반환합니다."""
    feed_list = feeds or DEFAULT_FEEDS
    seen_links: set[str] = set()
    by_section: dict[str, list[dict]] = {}

    for feed in feed_list:
        section = feed["section"]
        by_section[section] = fetch_today_for_feed(
            feed,
            max_pages=max_pages,
            seen_links=seen_links,
        )

    return by_section
